"""
conftest.py - Shared fixtures for the pytest test suite.
"""

import pytest
from unittest.mock import MagicMock

from src.app import create_app

# --- Application Fixtures ---

@pytest.fixture(scope='module')
def app():
    """
    Fixture to create and configure a new app instance for each test module.
    """
    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "CACHE_TYPE": "SimpleCache",
    })
    yield flask_app

@pytest.fixture(scope='module')
def client(app):
    """
    Fixture to create a test client for making requests to the app.
    """
    return app.test_client()

@pytest.fixture
def authenticated_client(client, mocker, mock_spotify):
    """
    Fixture to create a test client that is already authenticated.
    This now uses the mock_spotify fixture to ensure consistent mock data.
    """
    # Patch the get_spotify_client function to return our configured mock_spotify instance.
    mocker.patch('src.routes.get_spotify_client', return_value=mock_spotify)
    yield client


# --- Mocking Fixtures ---

@pytest.fixture
def mock_spotify(mocker):
    """
    Fixture to mock the spotipy.Spotify client.
    """
    mock_sp = MagicMock()
    # Define a standard track dictionary for reuse
    track_data = {
        "id": "test_track_id",
        "name": "Test Song",
        "artists": [{"id": "test_artist_id", "name": "Test Artist"}],
        "album": {"id": "test_album_id", "images": [{"url": "http://example.com/image.jpg"}]}
    }
    mock_sp.track.return_value = track_data
    mock_sp.search.return_value = {"tracks": {"items": [track_data]}}
    # This mock is now ready to be used by other fixtures or tests
    return mock_sp

@pytest.fixture
def mock_genius(mocker):
    """
    Fixture to mock the lyricsgenius.Genius client.
    """
    mock_genius_instance = MagicMock()
    mock_genius_instance.search_songs.return_value = {
        "hits": [{
            "result": {
                "id": 123,
                "title": "Test Song",
                "primary_artist": {"name": "Test Artist"}
            }
        }]
    }
    mock_genius_instance.lyrics.return_value = "This is the original test lyric."
    mocker.patch('src.services.genius_services.lyricsgenius.Genius', return_value=mock_genius_instance)
    return mock_genius_instance

@pytest.fixture
def mock_celery_tasks(mocker):
    """
    Fixture to mock the .delay() method of all Celery tasks.
    """
    # We mock the tasks at the point where they are imported in the routes module
    mock_fetch = mocker.patch('src.routes.fetch_and_populate_task.delay')
    mock_youtube = mocker.patch('src.routes.fetch_youtube_task.delay')
    mock_translate = mocker.patch('src.routes.translate_and_update_cache_task.delay')
    mock_playlist = mocker.patch('src.routes.create_spotify_playlist_task.delay')
    
    return {
        "fetch": mock_fetch,
        "translate": mock_translate,
        "youtube": mock_youtube,
        "playlist": mock_playlist
    }