"""
Celery Worker Module

This module defines the background tasks that the application can offload
to a separate worker process. It imports the shared Celery app instance.
"""
import logging
from deep_translator import GoogleTranslator
from src.extensions import celery_app
from src.utils.text_processors import format_processed_text, clean_genius_metadata, romanize_lyrics

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def fetch_and_populate_task(self, job_id, track_id, song_title, artist_name):
    """
    Primary background task to fetch Genius lyrics content for a track.
    Imports are done inside the task to ensure app context is available.
    """
    from src.app import create_app
    flask_app = create_app()
    with flask_app.app_context():
        from src.extensions import cache
        from src.services.genius_services import get_genius_client
        from src.services.youtube_services import search_youtube_video
        from src.utils.cache_manager import lfu_cache_manager

        cache_key = f"track_{track_id}"
        progress_key = f"priming:job:{job_id}" if job_id else None
        logger.info("Worker: Starting content fetch for track_id: %s", track_id)

        try:
            genius = get_genius_client()
            search_term = f"{song_title} {artist_name}"
            search_results = genius.search_songs(search_term)
            lyrics_text = None
            if search_results and search_results.get('hits'):
                hits = search_results['hits']
                sorted_hits = sorted(hits, key=lambda h: len(h['result']['title']))
                for hit in sorted_hits:
                    result = hit['result']
                    if artist_name.lower() in result['primary_artist']['name'].lower() and song_title.lower() in result['title'].lower():
                        lyrics_text = genius.lyrics(result['id'])
                        if lyrics_text:
                            break
            
            lyrics_not_found_msg = "Lyrics not found for this track."
            original_lyrics = lyrics_not_found_msg
            romanized_lyrics = lyrics_not_found_msg

            if lyrics_text:
                cleaned_lyrics = clean_genius_metadata(lyrics_text)
                original_lyrics = cleaned_lyrics
                romanized_lyrics = romanize_lyrics(cleaned_lyrics)
                translate_and_update_cache_task.delay(track_id, cleaned_lyrics)
            
            fetch_youtube_task.delay(track_id, song_title, artist_name)
            
            content = cache.get(cache_key)
            if content:
                content.update({
                    "original_lyrics": original_lyrics,
                    "romanized_lyrics": romanized_lyrics,
                })
                
                is_favorite = lfu_cache_manager.redis.sismember(lfu_cache_manager.FAVORITES_KEY, cache_key)
                timeout = 0 if is_favorite else flask_app.config.get("CACHE_DEFAULT_TIMEOUT")
                cache.set(cache_key, content, timeout=timeout)
                logger.info("Worker: Populated lyrics for track_id: %s", track_id)

        except Exception as e:
            logger.error("Worker: Failed to fetch lyrics for track_id '%s': %s", track_id, e, exc_info=True)
            content = cache.get(cache_key)
            if content:
                content.update({
                    "original_lyrics": "An error occurred while fetching lyrics.",
                    "romanized_lyrics": "An error occurred.",
                })
                cache.set(cache_key, content)
        finally:
            if progress_key:
                lfu_cache_manager.redis.incr(progress_key)


@celery_app.task
def fetch_youtube_task(track_id, song_title, artist_name):
    """
    A dedicated Celery task to fetch a YouTube URL and update the cache.
    """
    from src.app import create_app
    flask_app = create_app()
    with flask_app.app_context():
        from src.extensions import cache
        from src.services.youtube_services import search_youtube_video
        from src.utils.cache_manager import lfu_cache_manager

        cache_key = f"track_{track_id}"
        logger.info("Worker: Starting YouTube fetch for track_id: %s", track_id)
        
        try:
            youtube_url = search_youtube_video(song_title, artist_name)
            content = cache.get(cache_key)
            if content:
                content['youtube_url'] = youtube_url
                is_favorite = lfu_cache_manager.redis.sismember(lfu_cache_manager.FAVORITES_KEY, cache_key)
                timeout = 0 if is_favorite else flask_app.config.get("CACHE_DEFAULT_TIMEOUT")
                cache.set(cache_key, content, timeout=timeout)
                logger.info("Worker: Successfully updated YouTube URL for track_id: %s", track_id)
        except Exception as e:
            logger.error("Worker: Failed to fetch YouTube URL for track_id '%s': %s", track_id, e, exc_info=True)
            content = cache.get(cache_key)
            if content:
                content['youtube_url'] = flask_app.config["FALLBACK_YOUTUBE_URL"]
                cache.set(cache_key, content)


@celery_app.task
def translate_and_update_cache_task(track_id, text_to_translate):
    """
    A Celery task to translate lyrics in the background and update the cache.
    """
    from src.app import create_app
    flask_app = create_app()
    with flask_app.app_context():
        from src.extensions import cache
        from src.utils.cache_manager import lfu_cache_manager
        
        cache_key = f"track_{track_id}"
        logger.info("Worker: Starting translation for track_id: %s", track_id)
        
        try:
            raw_translation = GoogleTranslator(source='auto', target='en').translate(text_to_translate)
            translated_lyrics = format_processed_text(raw_translation)
            
            content = cache.get(cache_key)
            if content:
                content['translated_lyrics'] = translated_lyrics
                
                is_favorite = lfu_cache_manager.redis.sismember(lfu_cache_manager.FAVORITES_KEY, cache_key)
                timeout = 0 if is_favorite else flask_app.config.get("CACHE_DEFAULT_TIMEOUT")
                cache.set(cache_key, content, timeout=timeout)
                
                logger.info("Worker: Successfully translated and updated cache for track_id: %s", track_id)
            else:
                logger.warning("Worker: Could not find content in cache for key %s. Translation will be lost.", cache_key)

        except Exception as e:
            logger.error("Worker: Failed to translate lyrics for track_id '%s': %s", track_id, e, exc_info=True)
            content = cache.get(cache_key)
            if content:
                content['translated_lyrics'] = "Translation failed."
                cache.set(cache_key, content)


@celery_app.task
def create_spotify_playlist_task(token_info, track_ids, playlist_name):
    """
    A Celery task to create a Spotify playlist and add tracks to it.
    """
    from src.app import create_app
    from spotipy import Spotify
    
    flask_app = create_app()
    with flask_app.app_context():
        try:
            sp = Spotify(auth=token_info['access_token'])
            user_id = sp.current_user()['id']

            playlist_description = "Playlist created by Spotify Romanizer."
            new_playlist = sp.user_playlist_create(
                user=user_id, name=playlist_name, public=True, description=playlist_description
            )
            playlist_id = new_playlist['id']

            if track_ids:
                track_uris = [f"spotify:track:{tid}" for tid in track_ids]
                for i in range(0, len(track_uris), 100):
                    chunk = track_uris[i:i + 100]
                    sp.playlist_add_items(playlist_id, chunk)
            
            logger.info("Worker: Successfully created playlist '%s' and added %d tracks for user %s.", 
                        playlist_name, len(track_ids), user_id)

        except Exception as e:
            logger.error("Worker: Failed to create playlist for user. Error: %s", e, exc_info=True)


@celery_app.task
def priming_complete_callback_task(results, job_id):
    """
    This task is called by a Celery chord after all priming tasks are complete.
    Its job is to clean up the progress tracking key from Redis.
    """
    from src.utils.cache_manager import lfu_cache_manager
    
    progress_key = f"priming:job:{job_id}"
    lfu_cache_manager.redis.expire(progress_key, 60)
    
    logger.info("Worker: Bulk cache priming job %s completed.", job_id)
    return {"status": "complete", "job_id": job_id}