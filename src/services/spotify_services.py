"""
Spotify Services Module

This module provides functions for interacting with the Spotify API.
It includes utilities for creating an authenticated Spotify client, revoking tokens,
performing track searches, and fetching artist, album, and playlist details.
"""

import logging
import requests
from datetime import datetime
from flask import current_app
from spotipy import Spotify
from src.utils.cache_manager import lfu_cache_manager

logger = logging.getLogger(__name__)


def get_spotify_client():
    """
    Get an authenticated Spotify client using the current app's OAuth.
    """
    try:
        token_info = current_app.sp_oauth.cache_handler.get_cached_token()
        if not token_info or not current_app.sp_oauth.validate_token(token_info):
            logger.warning("Invalid or missing Spotify token. Re-authentication may be required.")
            return None
        return Spotify(auth_manager=current_app.sp_oauth)
    except Exception as e:
        logger.error("Could not create Spotify client: %s", e)
        return None


def revoke_spotify_token(access_token, client_id, client_secret):
    """
    Revoke a Spotify access token.
    """
    revoke_url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": access_token,
        "token_type_hint": "access_token",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        response = requests.post(revoke_url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        logger.info("Spotify access token revoked successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error("Error revoking Spotify access token: %s", e)
        return False


def _format_spotify_track(track_item, album_image_lg=None, album_image_sm=None):
    """
    Private helper to format a Spotify track item into a standard dictionary.
    """
    if not track_item:
        return None

    if album_image_lg is None or album_image_sm is None:
        images = track_item.get("album", {}).get("images", [])
        album_image_lg = images[0]["url"] if images else ""
        album_image_sm = images[-1]["url"] if images else ""

    return {
        "track_id": track_item["id"],
        "title": track_item["name"],
        "artist": track_item["artists"][0]["name"],
        "artist_id": track_item["artists"][0]["id"],
        "album_id": track_item.get("album", {}).get("id"),
        "image_url_sm": album_image_sm,
        "image_url_lg": album_image_lg,
    }


def perform_spotify_search(sp_client, query):
    """
    Execute Spotify search and format results with all necessary IDs and images.
    """
    try:
        results = sp_client.search(q=query, type="track", limit=10, market="JP")
        return [_format_spotify_track(track) for track in results.get("tracks", {}).get("items", [])]
    except Exception as e:
        logger.error("An error occurred during Spotify search for query '%s': %s", query, e)
        return []


def add_tracks_to_playlist(sp_client, playlist_id, track_ids):
    """
    Adds a list of tracks to a specified playlist, ensuring no duplicates are added.
    Returns a dictionary with the count of added and skipped (duplicate) tracks.
    """
    if not all([playlist_id, track_ids]):
        return {"success": False, "added": 0, "skipped": 0}

    try:
        playlist_details = get_playlist_details_and_tracks(sp_client, playlist_id)
        if not playlist_details:
            raise Exception("Could not fetch existing playlist details.")
        
        existing_track_ids = {track['track_id'] for track in playlist_details['tracks']}
        
        tracks_to_add_uris = [f"spotify:track:{tid}" for tid in track_ids if tid not in existing_track_ids]
        
        num_to_add = len(tracks_to_add_uris)
        num_skipped = len(track_ids) - num_to_add

        if num_to_add > 0:
            for i in range(0, num_to_add, 100):
                chunk = tracks_to_add_uris[i:i + 100]
                sp_client.playlist_add_items(playlist_id, chunk)
            logger.info("Added %d new tracks to playlist %s. Skipped %d duplicates.", num_to_add, playlist_id, num_skipped)
        else:
            logger.info("No new tracks to add to playlist %s. All %d selected tracks were duplicates.", playlist_id, num_skipped)

        return {"success": True, "added": num_to_add, "skipped": num_skipped}

    except Exception as e:
        logger.error("Failed to add tracks to playlist %s: %s", playlist_id, e)
        return {"success": False, "added": 0, "skipped": len(track_ids)}


def unfollow_playlist(sp_client, playlist_id):
    """
    Unfollows (deletes) a playlist for the current user.
    """
    try:
        sp_client.current_user_unfollow_playlist(playlist_id)
        logger.info("Successfully unfollowed playlist ID: %s", playlist_id)
        return True
    except Exception as e:
        logger.error("Failed to unfollow playlist ID %s: %s", playlist_id, e)
        return False


def remove_track_from_playlist(sp_client, playlist_id, track_id):
    """
    Removes all occurrences of a track from a specific playlist.
    This aligns with the "Set-like" playlist philosophy.
    """
    try:
        sp_client.playlist_remove_all_occurrences_of_items(playlist_id, [track_id])
        logger.info("Successfully removed all occurrences of track %s from playlist %s", track_id, playlist_id)

        playlist = sp_client.playlist(playlist_id, fields="tracks.total,images")
        remaining_tracks = playlist['tracks']['total']
        new_image_url = playlist['images'][0]['url'] if playlist.get('images') else None

        return {
            "success": True, 
            "remaining_tracks": remaining_tracks,
            "new_image_url": new_image_url
        }
    except Exception as e:
        logger.error("Failed to remove track %s from playlist %s: %s", track_id, playlist_id, e)
        return {"success": False, "remaining_tracks": -1, "new_image_url": None}


def rename_playlist(sp_client, playlist_id, new_name):
    """
    Renames a user's playlist.
    """
    try:
        sp_client.playlist_change_details(playlist_id, name=new_name)
        logger.info("Successfully renamed playlist %s to '%s'", playlist_id, new_name)
        return True
    except Exception as e:
        logger.error("Failed to rename playlist %s: %s", playlist_id, e)
        return False


def reorder_playlist_items(sp_client, playlist_id, range_start, insert_before):
    """
    Moves a track within a playlist to a new position and returns the new cover image.
    """
    try:
        sp_client.playlist_reorder_items(
            playlist_id=playlist_id,
            range_start=range_start,
            insert_before=insert_before,
            range_length=1
        )
        logger.info("Successfully reordered track in playlist %s", playlist_id)

        playlist = sp_client.playlist(playlist_id, fields="images")
        new_image_url = playlist['images'][0]['url'] if playlist.get('images') else None
        
        return {"success": True, "new_image_url": new_image_url}
    except Exception as e:
        logger.error("Failed to reorder track in playlist %s: %s", playlist_id, e)
        return {"success": False, "error": "Failed to reorder track on Spotify."}


def get_user_playlist_order(sp_client):
    """
    Retrieves the user's custom playlist order from Redis.
    """
    try:
        user_id = sp_client.current_user()['id']
        redis_key = f"user:{user_id}:playlist_order"
        ordered_ids = lfu_cache_manager.redis.lrange(redis_key, 0, -1)
        return ordered_ids
    except Exception as e:
        logger.error("Could not retrieve playlist order for user: %s", e)
        return []


def save_user_playlist_order(sp_client, playlist_ids):
    """
    Saves a new custom playlist order for the user in Redis.
    """
    try:
        user_id = sp_client.current_user()['id']
        redis_key = f"user:{user_id}:playlist_order"
        
        pipe = lfu_cache_manager.redis.pipeline()
        pipe.delete(redis_key)
        if playlist_ids:
            pipe.rpush(redis_key, *playlist_ids)
        pipe.execute()
        
        logger.info("Saved new playlist order for user %s", user_id)
        return True
    except Exception as e:
        logger.error("Could not save playlist order for user: %s", e)
        return False


def get_user_playlists(sp_client):
    """
    Fetches all of the current user's playlists, sorted by their custom order.
    """
    try:
        spotify_playlists = []
        results = sp_client.current_user_playlists()
        while results:
            for item in results.get("items", []):
                spotify_playlists.append({
                    "id": item["id"],
                    "name": item["name"],
                    "image_url": item["images"][0]["url"] if item.get("images") else "",
                    "owner": item["owner"]["display_name"],
                    "total_tracks": item["tracks"]["total"]
                })
            results = sp_client.next(results) if results.get('next') else None
        
        custom_order = get_user_playlist_order(sp_client)
        
        if not custom_order:
            return spotify_playlists

        playlist_map = {p['id']: p for p in spotify_playlists}
        sorted_playlists = []
        
        for pid in custom_order:
            if pid in playlist_map:
                sorted_playlists.append(playlist_map.pop(pid))
        
        sorted_playlists.extend(playlist_map.values())
        
        return sorted_playlists
        
    except Exception as e:
        logger.error("Failed to get user playlists: %s", e)
        return []


def get_artist_details_and_top_tracks(sp_client, artist_id):
    """
    Fetches artist details and their top tracks from Spotify.
    """
    try:
        artist_data = sp_client.artist(artist_id)
        artist_info = {
            "id": artist_id, # Pass the ID for the new API endpoint
            "name": artist_data.get("name"),
            "image_url": artist_data["images"][0]["url"] if artist_data.get("images") else "",
            "genres": artist_data.get("genres", [])
        }

        top_tracks_data = sp_client.artist_top_tracks(artist_id, country="JP")
        top_tracks = [_format_spotify_track(track) for track in top_tracks_data.get("tracks", [])]

        return {"artist_info": artist_info, "top_tracks": top_tracks}
    except Exception as e:
        logger.error("Failed to get artist details for ID %s: %s", artist_id, e)
        return None


def get_artist_albums(sp_client, artist_id):
    """
    Fetches all of an artist's albums and singles, handling pagination.
    """
    albums = []
    try:
        results = sp_client.artist_albums(artist_id, album_type='album,single', limit=50)
        while results:
            for item in results.get("items", []):
                albums.append({
                    "id": item["id"],
                    "name": item["name"],
                    "image_url": item["images"][0]["url"] if item.get("images") else "",
                    "release_date": item.get("release_date", "").split('-')[0],
                    "album_type": item.get("album_type", "album").capitalize()
                })
            results = sp_client.next(results) if results.get('next') else None
        return albums
    except Exception as e:
        logger.error("Failed to get artist albums for ID %s: %s", artist_id, e)
        return []


def get_album_details_and_tracks(sp_client, album_id):
    """
    Fetches album details and its full tracklist from Spotify, handling pagination.
    """
    try:
        album_data = sp_client.album(album_id)
        
        album_info = {
            "name": album_data.get("name"),
            "artist_name": album_data["artists"][0]["name"],
            "artist_id": album_data["artists"][0]["id"],
            "release_date": album_data.get("release_date"),
            "image_url": album_data["images"][0]["url"] if album_data.get("images") else "",
            # Calculate total duration
            "total_duration_ms": sum(track['duration_ms'] for track in album_data.get("tracks", {}).get("items", []))
        }
        
        image_url_lg = album_info["image_url"]
        image_url_sm = album_data["images"][-1]["url"] if album_data.get("images") else ""

        tracks = []
        results = album_data.get("tracks", {})
        while results:
            tracks.extend([_format_spotify_track(track, image_url_lg, image_url_sm) for track in results.get("items", [])])
            results = sp_client.next(results) if results.get('next') else None

        return {"album_info": album_info, "tracks": tracks}
    except Exception as e:
        logger.error("Missing expected data in Spotify album response for ID %s: %s", album_id, e)
        return None


def get_playlist_details_and_tracks(sp_client, playlist_id):
    """
    Fetches a specific playlist's details and all of its tracks, handling pagination.
    """
    try:
        playlist_data = sp_client.playlist(playlist_id)
        playlist_info = {
            "id": playlist_id,
            "name": playlist_data.get("name"),
            "description": playlist_data.get("description"),
            "image_url": playlist_data["images"][0]["url"] if playlist_data.get("images") else ""
        }

        tracks = []
        results = playlist_data.get("tracks", {})
        while results:
            for item in results.get("items", []):
                track = _format_spotify_track(item.get("track"))
                if track:
                    tracks.append(track)
            results = sp_client.next(results) if results.get('next') else None
        
        return {"playlist_info": playlist_info, "tracks": tracks}
    except Exception as e:
        logger.error("Failed to get playlist details for ID %s: %s", playlist_id, e)
        return None