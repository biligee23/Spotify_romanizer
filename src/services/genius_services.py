"""
This module provides services for fetching and caching lyrics and track content 
from Genius and YouTube using utility functions for cleaning and romanizing lyrics.
"""

# Standard library imports
import logging

# Third-party imports
import lyricsgenius
from flask import current_app

# Local application imports
from src.celery_worker import fetch_and_populate_task
from src.utils.cache_manager import lfu_cache_manager

logger = logging.getLogger(__name__)

genius_client = None

def get_genius_client():
    """Initializes and returns a singleton Genius API client."""
    global genius_client
    if genius_client is None:
        token = current_app.config.get("GENIUS_ACCESS_TOKEN")
        if not token:
            raise ValueError("GENIUS_ACCESS_TOKEN is not configured.")
        genius_client = lyricsgenius.Genius(token, verbose=False, timeout=15)
    return genius_client

def create_skeleton_cache_entry(track_id, song_title, artist_name, album_id, artist_id, image_url):
    """
    Creates an initial 'skeleton' cache entry with placeholders.
    """
    logger.info("Creating skeleton cache for track_id: %s", track_id)
    
    content = {
        "track_id": track_id,
        "song_title": song_title,
        "artist_name": artist_name,
        "artist_id": artist_id,
        "album_id": album_id,
        "image_url": image_url,
        "original_lyrics": "Loading lyrics...",
        "romanized_lyrics": "Loading...",
        "translated_lyrics": "Loading...",
        "youtube_url": ""
    }

    cache_key = f"track_{track_id}"
    lfu_cache_manager.set(cache_key, content)
    return content