"""
YouTube Services Module

This module provides functions for interacting with the YouTube API, 
including searching for videos by song title and artist name.
"""

# Standard library imports
import logging

# Third-party imports
import requests
from flask import current_app

logger = logging.getLogger(__name__)


def search_youtube_video(song_title, artist_name):
    """
    Search for a YouTube video using the song title and artist name.
    """
    query = f"{song_title} {artist_name}"
    try:
        api_key = current_app.config["YOUTUBE_API_KEY"]
        youtube_api_url = (
            f"https://www.googleapis.com/youtube/v3/search?"
            f"part=snippet&q={query}&key={api_key}&type=video&maxResults=1"
        )

        response = requests.get(youtube_api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("items"):
            video_id = data["items"][0]["id"]["videoId"]
            logger.info("Found YouTube video ID %s for '%s'", video_id, query)
            return f"https://www.youtube.com/embed/{video_id}"

    except requests.exceptions.RequestException as e:
        logger.error("Error searching YouTube video for '%s': %s", query, e)
    except (KeyError, IndexError) as e:
        logger.error("Error parsing YouTube API response for '%s': %s", query, e)

    logger.warning("Could not find YouTube video for '%s'. Using fallback.", query)
    return current_app.config["FALLBACK_YOUTUBE_URL"]