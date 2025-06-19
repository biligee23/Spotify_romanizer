"""
Routes Module
This module defines the routes for the Spotify Romanizer application.
"""
import logging
import uuid
from flask import (
    Blueprint,
    request,
    redirect,
    session,
    url_for,
    render_template,
    current_app,
    flash,
    jsonify,
    g # Import the request-bound global object 'g'
)
from src.services.spotify_services import (
    get_spotify_client,
    revoke_spotify_token,
    perform_spotify_search,
    add_tracks_to_playlist,
    unfollow_playlist,
    remove_track_from_playlist,
    rename_playlist,
    reorder_playlist_items,
    save_user_playlist_order,
    get_artist_details_and_top_tracks,
    get_artist_albums,
    get_album_details_and_tracks,
    get_user_playlists,
    get_playlist_details_and_tracks,
)
from src.services.genius_services import create_skeleton_cache_entry
from src.utils.cache_manager import lfu_cache_manager
from src.extensions import cache
from src.celery_worker import (
    create_spotify_playlist_task, 
    fetch_and_populate_task, 
    fetch_youtube_task,
    translate_and_update_cache_task
)

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.before_request
def before_request_auth():
    """
    Run before every request in this blueprint.
    - Checks if the user is authenticated.
    - Attaches the authenticated Spotify client to the request global 'g'.
    - Redirects to login if authentication is required and not present.
    """
    # Define endpoints that do NOT require authentication
    unprotected_endpoints = ['main.home', 'main.login', 'main.callback', 'main.logout', 'static']
    
    if request.endpoint in unprotected_endpoints:
        return

    # For all other endpoints, require authentication
    g.sp = get_spotify_client()
    if g.sp is None:
        flash("Your session has expired. Please log in again.", "info")
        return redirect(url_for("main.home"))


@main_bp.route("/")
def home():
    """
    Landing page. If already logged in (checked by before_request),
    it will redirect. If not, it shows the login page.
    """
    # The before_request hook doesn't run on the home page itself,
    # so we do a manual check here to redirect if already logged in.
    if get_spotify_client():
        return redirect(url_for("main.search"))
    return render_template("login.html")


@main_bp.route("/login")
def login():
    """Redirects the user to the Spotify authorization page."""
    sp_oauth = current_app.sp_oauth
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@main_bp.route("/callback")
def callback():
    """Handle Spotify OAuth callback and token acquisition."""
    try:
        current_app.sp_oauth.get_access_token(request.args["code"], check_cache=False)
        return redirect(url_for("main.search"))
    except Exception as e:
        logger.error("An error occurred during the OAuth callback: %s", e)
        flash("Authentication failed. Please try again.", "error")
        return redirect(url_for("main.home"))


@main_bp.route("/logout")
def logout():
    """Handle user logout and token revocation."""
    token_info = session.get("token_info", {})
    access_token = token_info.get("access_token")
    if access_token:
        try:
            revoke_spotify_token(
                access_token=access_token,
                client_id=current_app.config["SPOTIFY_CLIENT_ID"],
                client_secret=current_app.config["SPOTIFY_CLIENT_SECRET"],
            )
        except Exception as e:
            logger.error("Failed to revoke token: %s", e)
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for("main.home"))


@main_bp.route("/search", methods=["GET"])
def search():
    """Renders the main search page."""
    # No need to check for auth, before_request handles it.
    cached_data = lfu_cache_manager.get_formatted_lfu_list()
    return render_template(
        "search_form.html", 
        favorites=cached_data["favorites"],
        history=cached_data["history"]
    )


@main_bp.route("/api/search", methods=["GET"])
def api_search():
    """API endpoint for performing a Spotify search. Returns results as JSON."""
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Use g.sp, which is guaranteed to exist by before_request
    track_info = perform_spotify_search(g.sp, query)

    favorite_keys = lfu_cache_manager.redis.smembers(lfu_cache_manager.FAVORITES_KEY)
    for track in track_info:
        cache_key = f"track_{track['track_id']}"
        track['cache_key'] = cache_key
        track['is_favorite'] = cache_key in favorite_keys

    return jsonify(track_info)


@main_bp.route("/api/create_playlist", methods=["POST"])
def api_create_playlist():
    """
    API endpoint to create a new playlist. This is now asynchronous.
    """
    data = request.get_json()
    track_ids = data.get("track_ids")
    playlist_name = data.get("playlist_name")

    if not track_ids or not playlist_name:
        return jsonify({"success": False, "error": "Missing track IDs or playlist name"}), 400

    token_info = current_app.sp_oauth.cache_handler.get_cached_token()
    if not token_info:
        return jsonify({"success": False, "error": "Could not retrieve user token."}), 401

    create_spotify_playlist_task.delay(token_info, track_ids, playlist_name)
    
    return jsonify({"success": True, "message": "Playlist creation started in the background."})


@main_bp.route("/api/playlist/add_tracks", methods=["POST"])
def api_add_tracks_to_playlist():
    """
    API endpoint to add tracks to an existing playlist, preventing duplicates.
    """
    data = request.get_json()
    track_ids = data.get("track_ids")
    playlist_id = data.get("playlist_id")

    if not track_ids or not playlist_id:
        return jsonify({"success": False, "error": "Missing track IDs or playlist ID"}), 400

    result = add_tracks_to_playlist(g.sp, playlist_id, track_ids)

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify({"success": False, "error": "Failed to add tracks to playlist"}), 500


@main_bp.route("/api/cache/delete", methods=["POST"])
def delete_cache_item():
    """API endpoint to delete a specific item from the cache."""
    data = request.get_json()
    cache_key = data.get("cache_key")

    if not cache_key:
        return jsonify({"success": False, "error": "Missing cache_key"}), 400

    success = lfu_cache_manager.delete(cache_key)

    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to delete item"}), 500


@main_bp.route("/api/favorites/add", methods=["POST"])
def add_favorite():
    """API endpoint to add a song to favorites."""
    data = request.get_json()
    cache_key = data.get("cache_key")
    if not cache_key:
        return jsonify({"success": False, "error": "Missing cache_key"}), 400
    
    success = lfu_cache_manager.add_to_favorites(cache_key)
    return jsonify({"success": success})


@main_bp.route("/api/favorites/remove", methods=["POST"])
def remove_favorite():
    """API endpoint to remove a song from favorites."""
    data = request.get_json()
    cache_key = data.get("cache_key")
    if not cache_key:
        return jsonify({"success": False, "error": "Missing cache_key"}), 400
    
    success = lfu_cache_manager.remove_from_favorites(cache_key)
    return jsonify({"success": success})


@main_bp.route("/api/favorites/add_bulk", methods=["POST"])
def add_favorite_bulk():
    """API endpoint to add multiple songs to favorites."""
    data = request.get_json()
    cache_keys = data.get("cache_keys")
    if not cache_keys:
        return jsonify({"success": False, "error": "Missing cache_keys"}), 400
    
    success = lfu_cache_manager.add_to_favorites_bulk(cache_keys)
    return jsonify({"success": success})


@main_bp.route("/api/favorites/remove_bulk", methods=["POST"])
def remove_favorite_bulk():
    """API endpoint to remove multiple songs from favorites."""
    data = request.get_json()
    cache_keys = data.get("cache_keys")
    if not cache_keys:
        return jsonify({"success": False, "error": "Missing cache_keys"}), 400
    
    success = lfu_cache_manager.remove_from_favorites_bulk(cache_keys)
    return jsonify({"success": success})


@main_bp.route("/api/playlist/delete", methods=["POST"])
def delete_playlist():
    """API endpoint to unfollow (delete) a playlist."""
    data = request.get_json()
    playlist_id = data.get("playlist_id")

    if not playlist_id:
        return jsonify({"success": False, "error": "Missing playlist_id"}), 400

    success = unfollow_playlist(g.sp, playlist_id)

    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to delete playlist"}), 500


@main_bp.route("/api/playlist/track/delete", methods=["POST"])
def delete_playlist_track():
    """API endpoint to remove a track from a playlist."""
    data = request.get_json()
    playlist_id = data.get("playlist_id")
    track_id = data.get("track_id")

    if not all([playlist_id, track_id]):
        return jsonify({"success": False, "error": "Missing playlist_id or track_id"}), 400

    result = remove_track_from_playlist(g.sp, playlist_id, track_id)

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify({"success": False, "error": "Failed to remove track"}), 500


@main_bp.route("/api/playlist/rename", methods=["POST"])
def rename_playlist_route():
    """API endpoint to rename a playlist."""
    data = request.get_json()
    playlist_id = data.get("playlist_id")
    new_name = data.get("new_name")

    if not all([playlist_id, new_name]):
        return jsonify({"success": False, "error": "Missing playlist_id or new_name"}), 400

    success = rename_playlist(g.sp, playlist_id, new_name)

    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to rename playlist"}), 500


@main_bp.route("/api/playlist/reorder_items", methods=["POST"])
def reorder_playlist_track():
    """
    API endpoint to reorder a track in a playlist.
    """
    data = request.get_json()
    playlist_id = data.get("playlist_id")
    old_index = data.get("old_index")
    new_index = data.get("new_index")

    if None in [playlist_id, old_index, new_index] or old_index == new_index:
        return jsonify({"success": False, "error": "Missing or invalid parameters"}), 400

    insert_before = new_index
    if old_index < new_index:
        insert_before = new_index + 1
    
    result = reorder_playlist_items(
        sp_client=g.sp,
        playlist_id=playlist_id,
        range_start=old_index,
        insert_before=insert_before
    )
    
    return jsonify(result)


@main_bp.route("/api/playlists/save_order", methods=["POST"])
def save_playlist_order():
    """
    API endpoint to save the user's custom playlist order.
    """
    data = request.get_json()
    playlist_ids = data.get("playlist_ids")

    if playlist_ids is None:
        return jsonify({"success": False, "error": "Missing playlist_ids parameter"}), 400

    success = save_user_playlist_order(g.sp, playlist_ids)

    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to save playlist order."}), 500


@main_bp.route("/api/playlist/prime_cache/<playlist_id>", methods=["POST"])
def prime_playlist_cache(playlist_id):
    """
    Dispatches background tasks to fetch data for all uncached tracks in a playlist.
    """
    try:
        playlist_data = get_playlist_details_and_tracks(g.sp, playlist_id)
        if not playlist_data:
            return jsonify({"success": False, "error": "Playlist not found."}), 404

        tasks_to_run_args = []
        for track in playlist_data['tracks']:
            cache_key = f"track_{track['track_id']}"
            if cache.get(cache_key) is None:
                tasks_to_run_args.append({
                    "track_id": track['track_id'],
                    "song_title": track['title'],
                    "artist_name": track['artist']
                })
                create_skeleton_cache_entry(
                    track_id=track['track_id'], song_title=track['title'], artist_name=track['artist'],
                    album_id=track['album_id'], artist_id=track['artist_id'], image_url=track['image_url_lg']
                )

        if not tasks_to_run_args:
            return jsonify({"success": True, "message": "All tracks are already cached.", "tasks_dispatched": 0})

        job_id = str(uuid.uuid4())
        progress_key = f"priming:job:{job_id}"
        lfu_cache_manager.redis.set(progress_key, 0)
        lfu_cache_manager.redis.expire(progress_key, 3600)

        for args in tasks_to_run_args:
            fetch_and_populate_task.delay(job_id, args['track_id'], args['song_title'], args['artist_name'])

        return jsonify({
            "success": True, 
            "message": f"Priming tasks dispatched for {len(tasks_to_run_args)} tracks.",
            "tasks_dispatched": len(tasks_to_run_args),
            "job_id": job_id
        })

    except Exception as e:
        logger.error("Failed to prime cache for playlist %s: %s", playlist_id, e)
        return jsonify({"success": False, "error": "An internal error occurred."}), 500


@main_bp.route("/api/priming/status/<job_id>", methods=["GET"])
def get_priming_status(job_id):
    """
    Checks the progress of a priming job by reading a counter from Redis.
    """
    progress_key = f"priming:job:{job_id}"
    completed_count_str = lfu_cache_manager.redis.get(progress_key)
    
    if completed_count_str is None:
        return jsonify({"status": "UNKNOWN", "completed": 0})

    return jsonify({
        "status": "PENDING",
        "completed": int(completed_count_str),
    })


@main_bp.route("/api/artist/<artist_id>/albums")
def api_get_artist_albums(artist_id):
    """
    API endpoint to fetch all albums for a given artist.
    """
    albums = get_artist_albums(g.sp, artist_id)
    return jsonify(albums)


@main_bp.route("/api/playlists")
def api_playlists():
    """API endpoint to fetch the current user's playlists as JSON."""
    user_playlists = get_user_playlists(g.sp)
    return jsonify(user_playlists)


@main_bp.route("/track/<track_id>")
def track_details(track_id):
    """
    Display track details. Implements a "cache-first, self-healing" strategy.
    """
    cache_key = f"track_{track_id}"
    content = lfu_cache_manager.get(cache_key)

    if content is None:
        logger.info("Cache MISS for track_id: %s. Creating skeleton and dispatching all tasks.", track_id)
        try:
            track = g.sp.track(track_id)
            content = create_skeleton_cache_entry(
                track_id=track_id, song_title=track["name"], artist_name=track["artists"][0]["name"],
                album_id=track["album"]["id"], artist_id=track["artists"][0]["id"],
                image_url=track["album"]["images"][0]["url"] if track.get("album", {}).get("images") else ""
            )
            fetch_and_populate_task.delay(None, track_id, content['song_title'], content['artist_name'])
        except Exception as e:
            logger.error("Failed to fetch initial track data for %s: %s", track_id, e)
            flash("Could not retrieve track details from Spotify.", "error")
            return redirect(url_for("main.search"))
    
    else:
        logger.info("Cache HIT for track_id: %s. Performing health check.", track_id)
        if not content.get('youtube_url'):
            logger.info("Health check: YouTube URL missing for %s. Re-dispatching task.", track_id)
            fetch_youtube_task.delay(track_id, content['song_title'], content['artist_name'])
        
        translation_status = content.get('translated_lyrics', '').lower()
        if 'loading' in translation_status or 'in progress' in translation_status or 'failed' in translation_status:
            logger.info("Health check: Translation incomplete for %s. Re-dispatching task.", track_id)
            if 'not found' not in content.get('original_lyrics', '').lower() and 'loading' not in content.get('original_lyrics', '').lower():
                translate_and_update_cache_task.delay(track_id, content['original_lyrics'])

    return render_template("track_info.html", track_data=content)


@main_bp.route("/artist/<artist_id>")
def artist_page(artist_id):
    """Displays an artist's details and their top tracks."""
    artist_data = get_artist_details_and_top_tracks(g.sp, artist_id)

    if not artist_data:
        flash("Could not find artist information.", "error")
        return redirect(url_for("main.search"))

    return render_template(
        "artist_page.html",
        artist_info=artist_data["artist_info"],
        top_tracks=artist_data["top_tracks"]
    )


@main_bp.route("/album/<album_id>")
def album_page(album_id):
    """Displays an album's details and its tracklist."""
    album_data = get_album_details_and_tracks(g.sp, album_id)

    if not album_data:
        flash("Could not find album information.", "error")
        return redirect(url_for("main.search"))
    
    total_seconds = album_data['album_info']['total_duration_ms'] / 1000
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    album_data['album_info']['total_duration_formatted'] = f"{minutes} min {seconds} sec"

    return render_template(
        "album_page.html",
        album_info=album_data["album_info"],
        tracks=album_data["tracks"]
    )


@main_bp.route("/playlists")
def playlists():
    """Displays a list of the current user's playlists."""
    user_playlists = get_user_playlists(g.sp)
    return render_template("playlists.html", playlists=user_playlists)


@main_bp.route("/playlist/<playlist_id>")
def playlist_details(playlist_id):
    """Displays the tracks within a specific playlist."""
    playlist_data = get_playlist_details_and_tracks(g.sp, playlist_id)

    if not playlist_data:
        flash("Could not find playlist information.", "error")
        return redirect(url_for("main.playlists"))

    return render_template(
        "playlist_details.html",
        playlist_info=playlist_data["playlist_info"],
        tracks=playlist_data["tracks"]
    )


@main_bp.route("/api/track/status/<track_id>")
def track_status(track_id):
    """
    Checks the cache for a track's full content status.
    This is polled by the front-end to update skeleton loaders.
    """
    cache_key = f"track_{track_id}"
    content = cache.get(cache_key)

    if not content:
        return jsonify({"status": "error", "message": "Track not found in cache."}), 404

    is_lyrics_pending = "loading" in content.get("romanized_lyrics", "").lower()
    is_youtube_pending = not content.get("youtube_url")
    is_translation_pending = "loading" in content.get("translated_lyrics", "").lower() or \
                             "in progress" in content.get("translated_lyrics", "").lower()

    if not is_lyrics_pending and not is_youtube_pending and not is_translation_pending:
        return jsonify({
            "status": "complete",
            "data": content
        })
    
    return jsonify({
        "status": "pending",
        "data": content
    })