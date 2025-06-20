"""
tests/routes/test_main_routes.py - Integration tests for main page routes.
"""

from unittest.mock import MagicMock

def test_search_page_protected(client):
    """
    Test that accessing a protected page like /search without being logged in
    results in a redirect to the home page.
    """
    response = client.get('/search', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login with Spotify" in response.data

def test_search_page_authenticated(authenticated_client):
    """
    Test that an authenticated user can successfully access the /search page.
    """
    response = authenticated_client.get('/search')
    assert response.status_code == 200
    assert b"Your Library" in response.data

def test_track_details_cache_miss(authenticated_client, mocker, mock_spotify, mock_celery_tasks):
    """
    Test the 'cache miss' scenario for the track details page.
    It should create a skeleton entry and dispatch background tasks.
    """
    # Simulate the cache returning nothing
    mocker.patch('src.routes.cache.get', return_value=None)
    
    # Configure the mock_spotify object directly to avoid context errors
    mock_spotify.track.return_value = {
        "id": "test_track_id", "name": "Test Song",
        "artists": [{"id": "test_artist_id", "name": "Test Artist"}],
        "album": {"id": "test_album_id", "images": [{"url": "http://example.com/image.jpg"}]}
    }

    # Make the request
    response = authenticated_client.get('/track/test_track_id')
    
    # Assert that the page loaded successfully
    assert response.status_code == 200
    
    # CORRECTED: Assert that the skeleton loader class is present in the response,
    # instead of the old "Loading..." text.
    assert b'class="skeleton skeleton-text"' in response.data
    
    # Assert that the main background task was dispatched
    mock_celery_tasks['fetch'].assert_called_once_with(
        None, 'test_track_id', 'Test Song', 'Test Artist'
    )

def test_track_details_cache_hit_self_healing(authenticated_client, mocker, mock_celery_tasks):
    """
    Test the 'cache hit' scenario with incomplete data (self-healing).
    It should render the page and re-dispatch only the missing tasks.
    """
    cached_content = {
        "track_id": "test_track_id",
        "song_title": "Test Song",
        "artist_name": "Test Artist",
        "original_lyrics": "Some lyrics",
        "youtube_url": "",
        "translated_lyrics": "Translation failed."
    }
    mocker.patch('src.routes.cache.get', return_value=cached_content)
    
    response = authenticated_client.get('/track/test_track_id')
    
    assert response.status_code == 200
    assert b"Some lyrics" in response.data
    
    mock_celery_tasks['fetch'].assert_not_called()
    mock_celery_tasks['youtube'].assert_called_once_with(
        'test_track_id', 'Test Song', 'Test Artist'
    )
    mock_celery_tasks['translate'].assert_called_once_with(
        'test_track_id', 'Some lyrics'
    )