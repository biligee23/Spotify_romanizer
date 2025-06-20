"""
tests/routes/test_api_routes.py - Integration tests for API endpoints.
"""

import json
from unittest.mock import ANY

def test_api_search_route(authenticated_client, mock_spotify):
    """Test the /api/search endpoint."""
    response = authenticated_client.get('/api/search?query=test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0
    assert data[0]['title'] == 'Test Song'

def test_api_search_no_query(authenticated_client):
    """Test that the search endpoint returns a 400 error if no query is provided."""
    response = authenticated_client.get('/api/search')
    assert response.status_code == 400
    assert b"Query parameter is required" in response.data

def test_api_add_tracks_to_playlist(authenticated_client, mocker):
    """Test adding tracks to an existing playlist."""
    mock_add_tracks = mocker.patch('src.routes.add_tracks_to_playlist', return_value={"success": True, "added": 1, "skipped": 0})
    response = authenticated_client.post(
        '/api/playlist/add_tracks',
        data=json.dumps({'playlist_id': 'p1', 'track_ids': ['t1']}),
        content_type='application/json'
    )
    assert response.status_code == 200
    mock_add_tracks.assert_called_once()

def test_api_create_playlist(authenticated_client, mocker, mock_celery_tasks):
    """Test dispatching the create playlist task."""
    with authenticated_client.application.app_context():
        mocker.patch('flask.current_app.sp_oauth.cache_handler.get_cached_token', return_value={'access_token': 'test-token'})
    
    response = authenticated_client.post(
        '/api/create_playlist',
        data=json.dumps({'playlist_name': 'New Playlist', 'track_ids': ['t1']}),
        content_type='application/json'
    )
    assert response.status_code == 200
    mock_celery_tasks['playlist'].assert_called_once()

def test_api_delete_playlist(authenticated_client, mocker):
    """Test deleting a playlist."""
    mock_unfollow = mocker.patch('src.routes.unfollow_playlist', return_value=True)
    response = authenticated_client.post(
        '/api/playlist/delete',
        data=json.dumps({'playlist_id': 'p1'}),
        content_type='application/json'
    )
    assert response.status_code == 200
    mock_unfollow.assert_called_once_with(ANY, 'p1')

def test_api_rename_playlist(authenticated_client, mocker):
    """Test renaming a playlist."""
    mock_rename = mocker.patch('src.routes.rename_playlist', return_value=True)
    response = authenticated_client.post(
        '/api/playlist/rename',
        data=json.dumps({'playlist_id': 'p1', 'new_name': 'New Name'}),
        content_type='application/json'
    )
    assert response.status_code == 200
    mock_rename.assert_called_once_with(ANY, 'p1', 'New Name')

def test_api_rename_playlist_missing_data(authenticated_client):
    """Test that renaming fails if required data is missing."""
    response = authenticated_client.post(
        '/api/playlist/rename',
        data=json.dumps({'playlist_id': 'p1'}), # Missing new_name
        content_type='application/json'
    )
    assert response.status_code == 400

def test_api_save_playlist_order(authenticated_client, mocker):
    """Test saving the custom playlist order."""
    mock_save_order = mocker.patch('src.routes.save_user_playlist_order', return_value=True)
    response = authenticated_client.post(
        '/api/playlists/save_order',
        data=json.dumps({'playlist_ids': ['p2', 'p1']}),
        content_type='application/json'
    )
    assert response.status_code == 200
    mock_save_order.assert_called_once_with(ANY, ['p2', 'p1'])

def test_api_prime_cache(authenticated_client, mocker):
    """Test the bulk cache priming endpoint."""
    mock_track = {
        'track_id': 't1', 'title': 'Test Title', 'artist': 'Test Artist',
        'album_id': 'a1', 'artist_id': 'ar1', 'image_url_lg': 'url'
    }
    mocker.patch('src.routes.get_playlist_details_and_tracks', return_value={'tracks': [mock_track]})
    mocker.patch('src.routes.cache.get', return_value=None)
    mock_create_skeleton = mocker.patch('src.routes.create_skeleton_cache_entry')
    mocker.patch('src.routes.fetch_and_populate_task.delay')

    response = authenticated_client.post('/api/playlist/prime_cache/p1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['tasks_dispatched'] == 1
    mock_create_skeleton.assert_called_once()