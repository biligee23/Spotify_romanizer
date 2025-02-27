# ============================
# IMPORTS AND ENVIRONMENT SETUP
# ============================

import os
from dotenv import load_dotenv
from flask import Flask, request, redirect, session, url_for, render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
import lyricsgenius
import pykakasi
import jaconv
import re
import requests
import logging

# Load environment variables from .env file
load_dotenv()

# Initialize Kakasi (Japanese text romanizer)
kks = pykakasi.kakasi()

# Fetch sensitive credentials from environment variables
GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_ACCESS_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Validate that all required environment variables are present
required_env_vars = ['GENIUS_ACCESS_TOKEN', 'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'YOUTUBE_API_KEY']
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# SPOTIFY AUTHENTICATION CONFIGURATION
# ============================

# Spotify OAuth configuration
redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private user-library-read user-read-playback-state user-modify-playback-state app-remote-control'
cache_handler = FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

# Helper function to get the Spotify object
def get_spotify():
    """Retrieve a valid Spotify client object or return None if authentication fails."""
    token_info = cache_handler.get_cached_token()
    if not token_info or not sp_oauth.validate_token(token_info):
        return None
    return Spotify(auth_manager=sp_oauth)

# ============================
# YOUTUBE VIDEO SEARCH
# ============================

def search_youtube_video(song_title, artist_name):
    """
    Search for a YouTube video using the song title and artist name.
    Returns the URL of the first matching video or a fallback video if no match is found.
    """
    query = f"{song_title} {artist_name}"
    youtube_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(youtube_url)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and data['items']:
                video_id = data['items'][0]['id']['videoId']
                return f"https://www.youtube.com/embed/{video_id}"
    except Exception as e:
        logger.error(f"Error searching YouTube video: {e}")
    
    # Fallback video URL
    return "https://www.youtube.com/embed/dQw4w9WgXcQ"

# ============================
# LYRICS PROCESSING FUNCTIONS
# ============================

def romanize_lyrics(lyrics):
    """
    Convert Japanese lyrics to Romanized form using Kakasi.
    Handles errors gracefully by logging them and appending an error message to the output.
    """
    romanized_lyrics = []
    for line in lyrics.split("\n"):
        if any(('\u3040' <= c <= '\u30ff') or ('\uff66' <= c <= '\uff9f') or ('\u4e00' <= c <= '\u9fff') for c in line):
            try:
                romaji_line = ' '.join([item['hepburn'] for item in kks.convert(line)])
                romaji_line = jaconv.kata2hira(romaji_line)  # Convert Katakana to Hiragana
                romanized_lyrics.append(romaji_line)
            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")
                romanized_lyrics.append(f"[Error processing line: {line}]")
        else:
            romanized_lyrics.append(line)
    return "\n".join(romanized_lyrics)

def clean_lyrics(lyrics):
    """
    Remove unwanted lines (e.g., contributors, translations) up to the first occurrence of 'lyrics'.
    """
    return re.sub(r'^.*?lyrics', '', lyrics, flags=re.IGNORECASE | re.DOTALL).strip()

def get_lyrics(song_title, artist_name):
    """
    Fetch lyrics from Genius API and romanize them if necessary.
    Returns the cleaned and romanized lyrics or a message if no lyrics are found.
    """
    genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
    genius.remove_section_headers = True  # Remove extra metadata
    try:
        song = genius.search_song(song_title, artist_name, get_full_info=True)
        if song:
            lyrics = song.lyrics
            cleaned_lyrics = clean_lyrics(lyrics)
            return romanize_lyrics(cleaned_lyrics)
    except Exception as e:
        logger.error(f"Error fetching lyrics from Genius: {e}")
    
    return f"Lyrics not found for {song_title} by {artist_name}. Try searching elsewhere!"

# ============================
# FLASK ROUTES
# ============================

@app.route('/')
def home():
    """
    Home route that redirects to Spotify login if not authenticated.
    """
    sp = get_spotify()
    if sp:
        return redirect(url_for('search'))
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """
    Handle the Spotify OAuth callback.
    """
    try:
        sp_oauth.get_access_token(request.args['code'])
    except Exception as e:
        logger.error(f"Error during Spotify OAuth callback: {e}")
    return redirect(url_for('search'))

@app.route('/search', methods=['GET'])
def search():
    """
    Search for a song and display clickable results.
    """
    sp = get_spotify()
    if not sp:
        return redirect(url_for('home'))
    
    query = request.args.get('query', '')
    if not query:
        return render_template('search_form.html')
    
    try:
        # Perform search query with Spotipy, targeting the Japanese market
        results = sp.search(q=query, type='track', limit=10, market='JP')
        tracks = results.get('tracks', {}).get('items', [])
        
        if not tracks:
            return render_template('search_form.html', message=f"No results found for '{query}'")
        
        # Create a list of tracks to display in the search result
        track_info = []
        for track in tracks:
            song_title = track['name']
            artist_name = track['artists'][0]['name']
            track_info.append({
                'song_title': song_title,
                'artist_name': artist_name,
                'track_id': track['id'],  # Use track ID to pass to the next page
            })
        
        return render_template('search_form.html', track_info=track_info)
    
    except Exception as e:
        logger.error(f"Error during search: {e}")
        return render_template('search_form.html', message=f"An error occurred: {e}")

@app.route('/track/<track_id>')
def track_details(track_id):
    """
    Display detailed information for a selected track, including lyrics and a YouTube video link.
    """
    sp = get_spotify()
    if not sp:
        return redirect(url_for('home'))
    
    try:
        # Get track details from Spotify API using track_id
        track = sp.track(track_id)
        song_title = track['name']
        artist_name = track['artists'][0]['name']
        image_url = track['album']['images'][0]['url'] if track['album']['images'] else ""
        
        # Get YouTube video URL and lyrics
        youtube_url = search_youtube_video(song_title, artist_name)
        lyrics = get_lyrics(song_title, artist_name)
        
        return render_template('track_info.html',
                               image_url=image_url,
                               song_title=song_title,
                               artist_name=artist_name,
                               youtube_url=youtube_url,
                               lyrics=lyrics)
    
    except Exception as e:
        logger.error(f"Error fetching track details: {e}")
        return f"An error occurred: {e}"

@app.route('/logout')
def logout():
    """
    Clear session, revoke Spotify access token, and log out.
    """
    # Get the access token from the session
    token_info = session.get('token_info', {})
    access_token = token_info.get('access_token')

    # Revoke the access token if it exists
    if access_token:
        revoke_url = 'https://accounts.spotify.com/api/token/revoke'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'token': access_token}
        try:
            response = requests.post(revoke_url, headers=headers, data=data)
            if response.status_code != 200:
                logger.warning("Failed to revoke Spotify access token.")
        except Exception as e:
            logger.error(f"Error revoking Spotify access token: {e}")

    # Clear the session
    session.clear()

    # Redirect to the home page
    return redirect(url_for('home'))

# ============================
# RUN THE APP
# ============================

if __name__ == '__main__':
    app.run(debug=True)