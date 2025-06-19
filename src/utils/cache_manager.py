"""
Cache Manager Module
This module provides a cache manager that handles both an LFU (Least Frequently Used)
cache for recent items and a permanent set for user favorites.
"""
import datetime
import logging
import redis
from flask import current_app
from src.extensions import cache
from src.config import Config

logger = logging.getLogger(__name__)


class LFUCacheManager:
    """
    A Cache Manager that handles both an LFU cache and a permanent favorites list.
    - Favorites are permanent: they do not expire and do not count towards the LFU cache limit.
    - History items are temporary: they are subject to LFU eviction and default timeouts.
    """

    ACCESS_COUNT_KEY = "track_access_counts"
    FAVORITES_KEY = "favorite_tracks"

    def __init__(self, max_entries=None):
        """
        Initialize the LFUCacheManager.
        """
        self.max_entries = max_entries or Config.CACHE_OPTIONS["MAX_ENTRIES"]
        try:
            self.redis = redis.Redis(
                host=Config.CACHE_REDIS_HOST,
                port=Config.CACHE_REDIS_PORT,
                decode_responses=True,
            )
            self.redis.ping()
            logger.info("LFUCacheManager connected to Redis successfully.")
        except redis.exceptions.RedisError as e:
            logger.error("Redis initialization error in LFUCacheManager: %s", e)
            self.redis = None

    def get(self, key):
        """
        Retrieve content from the cache and increment its access count.
        """
        if not self.redis:
            return None
        try:
            self.redis.zincrby(self.ACCESS_COUNT_KEY, 1, key)
            return cache.get(key)
        except redis.exceptions.RedisError as e:
            logger.error("Redis error during get operation for key '%s': %s", key, e)
        return None

    def set(self, key, content_dict):
        """
        Cache content and manage cache size by evicting the least used non-favorite item if full.
        Favorites do not count towards the max_entries limit.
        """
        if not self.redis:
            return
        try:
            all_keys = self.redis.zrange(self.ACCESS_COUNT_KEY, 0, -1)
            favorite_keys = self.redis.smembers(self.FAVORITES_KEY)
            non_favorite_count = len(set(all_keys) - favorite_keys)

            if non_favorite_count >= self.max_entries:
                potential_evictees = self.redis.zrange(self.ACCESS_COUNT_KEY, 0, 10)
                for key_to_evict in potential_evictees:
                    if key_to_evict not in favorite_keys:
                        self.delete(key_to_evict)
                        logger.info("Non-favorite cache full. Evicted least used key: %s", key_to_evict)
                        break

            content_dict["cached_at"] = datetime.datetime.now().isoformat()
            cache.set(key, content_dict)
            self.redis.zadd(self.ACCESS_COUNT_KEY, {key: 1})
            logger.info("Cached new content for key: %s", key)
        except redis.exceptions.RedisError as e:
            logger.error("Redis error during set operation for key '%s': %s", key, e)

    def delete(self, key):
        """
        Deletes an item from the cache, access tracking, and favorites.
        """
        if not self.redis:
            return False
        try:
            pipe = self.redis.pipeline()
            pipe.zrem(self.ACCESS_COUNT_KEY, key)
            pipe.srem(self.FAVORITES_KEY, key)
            cache.delete(key)
            pipe.execute()
            logger.info("Deleted cache key: %s", key)
            return True
        except redis.exceptions.RedisError as e:
            logger.error("Redis error during delete operation for key '%s': %s", key, e)
            return False

    def add_to_favorites(self, key):
        """
        Adds a cache key to the set of favorites and makes its cache entry permanent.
        """
        if not self.redis:
            return False
        try:
            self.redis.sadd(self.FAVORITES_KEY, key)
            
            content = cache.get(key)
            if content:
                cache.set(key, content, timeout=0)
                logger.info("Added key to favorites and made cache permanent: %s", key)
            else:
                logger.warning("Added key %s to favorites set, but no content found in cache.", key)
            return True
        except redis.exceptions.RedisError as e:
            logger.error("Redis error adding favorite for key '%s': %s", key, e)
            return False

    def remove_from_favorites(self, key):
        """
        Removes a cache key from favorites and reverts its cache entry to a default timeout.
        """
        if not self.redis:
            return False
        try:
            self.redis.srem(self.FAVORITES_KEY, key)

            content = cache.get(key)
            if content:
                default_timeout = current_app.config.get("CACHE_DEFAULT_TIMEOUT", 3600)
                cache.set(key, content, timeout=default_timeout)
                logger.info("Removed key from favorites and reverted to default timeout: %s", key)
            else:
                logger.warning("Removed key %s from favorites set, but no content found in cache to update.", key)
            return True
        except redis.exceptions.RedisError as e:
            logger.error("Redis error removing favorite for key '%s': %s", key, e)
            return False

    def add_to_favorites_bulk(self, keys):
        """
        Adds multiple keys to favorites efficiently.
        """
        if not self.redis or not keys:
            return False
        try:
            # SADD can take multiple arguments for a single, efficient operation
            self.redis.sadd(self.FAVORITES_KEY, *keys)
            # Iterate to make each cache entry permanent
            for key in keys:
                content = cache.get(key)
                if content:
                    cache.set(key, content, timeout=0)
            logger.info("Bulk added %d keys to favorites.", len(keys))
            return True
        except redis.exceptions.RedisError as e:
            logger.error("Redis error during bulk add to favorites: %s", e)
            return False

    def remove_from_favorites_bulk(self, keys):
        """
        Removes multiple keys from favorites efficiently.
        """
        if not self.redis or not keys:
            return False
        try:
            # SREM can take multiple arguments for a single, efficient operation
            self.redis.srem(self.FAVORITES_KEY, *keys)
            # Iterate to revert each cache entry to a default timeout
            default_timeout = current_app.config.get("CACHE_DEFAULT_TIMEOUT", 3600)
            for key in keys:
                content = cache.get(key)
                if content:
                    cache.set(key, content, timeout=default_timeout)
            logger.info("Bulk removed %d keys from favorites.", len(keys))
            return True
        except redis.exceptions.RedisError as e:
            logger.error("Redis error during bulk remove from favorites: %s", e)
            return False

    def get_formatted_lfu_list(self):
        """
        Retrieve and format cached songs, separating favorites from history.
        Both lists remain sorted by access count.
        """
        if not self.redis:
            return {"favorites": [], "history": []}
        
        favorites = []
        history = []
        try:
            track_keys = self.redis.zrange(
                self.ACCESS_COUNT_KEY, 0, -1, desc=True, withscores=True
            )
            favorite_keys = self.redis.smembers(self.FAVORITES_KEY)
            
            for key, score in track_keys:
                content = cache.get(key)
                if content and content.get("track_id"):
                    song_data = self._format_song_data(key, content, score)
                    is_favorite = key in favorite_keys
                    song_data["is_favorite"] = is_favorite
                    
                    if is_favorite:
                        favorites.append(song_data)
                    else:
                        history.append(song_data)
            
        except Exception as e:
            logger.error(f"An unexpected error occurred formatting cached songs: {e}", exc_info=True)
            
        return {"favorites": favorites, "history": history}

    def _format_song_data(self, key, content, score=None):
        """Helper function to format song data from cache content."""
        song_data = {
            "cache_key": key,
            "title": content.get("song_title", "Unknown Title"),
            "artist": content.get("artist_name", "Unknown Artist"),
            "cached_at": content.get("cached_at"),
            "track_id": content.get("track_id"),
            "image_url": content.get("image_url", ""),
            "artist_id": content.get("artist_id"),
            "album_id": content.get("album_id")
        }
        if score is not None:
            song_data["access_count"] = int(score)
        return song_data

# Create a single, shared instance of the cache manager for the application to use.
lfu_cache_manager = LFUCacheManager()