"""
tests/services/test_spotify_services.py - Unit tests for Spotify service functions.
"""

from unittest.mock import MagicMock

from src.services.spotify_services import add_tracks_to_playlist, get_user_playlists

def test_add_tracks_to_playlist_no_duplicates(mocker):
    """
    Test that add_tracks_to_playlist correctly identifies and adds only new tracks.
    """
    mock_sp = MagicMock()
    track_ids_to_add = ["track1", "track3"]
    
    # Mock the get_playlist_details_and_tracks function to control its output
    mocker.patch(
        'src.services.spotify_services.get_playlist_details_and_tracks',
        return_value={"tracks": [{"track_id": "track2"}]}
    )

    result = add_tracks_to_playlist(mock_sp, "p1", track_ids_to_add)

    assert result["success"] is True
    assert result["added"] == 2
    assert result["skipped"] == 0
    mock_sp.playlist_add_items.assert_called_once_with("p1", ["spotify:track:track1", "spotify:track:track3"])

def test_add_tracks_with_duplicates(mocker):
    """
    Test that the function correctly skips tracks that are already in the playlist.
    """
    mock_sp = MagicMock()
    track_ids_to_add = ["track1", "track2", "track3"]
    
    mocker.patch(
        'src.services.spotify_services.get_playlist_details_and_tracks',
        return_value={"tracks": [{"track_id": "track2"}]}
    )

    result = add_tracks_to_playlist(mock_sp, "p1", track_ids_to_add)

    assert result["success"] is True
    assert result["added"] == 2
    assert result["skipped"] == 1
    mock_sp.playlist_add_items.assert_called_once_with("p1", ["spotify:track:track1", "spotify:track:track3"])

def test_get_user_playlists_custom_order(mocker):
    """
    Test that get_user_playlists correctly re-sorts playlists based on a custom order from Redis.
    """
    mock_sp = MagicMock()
    mock_sp.current_user_playlists.return_value = {
        "items": [
            {"id": "pA", "name": "Playlist A", "images": [], "owner": {"display_name": "user"}, "tracks": {"total": 1}},
            {"id": "pB", "name": "Playlist B", "images": [], "owner": {"display_name": "user"}, "tracks": {"total": 1}},
            {"id": "pC", "name": "Playlist C", "images": [], "owner": {"display_name": "user"}, "tracks": {"total": 1}},
        ],
        "next": None
    }
    
    mocker.patch('src.services.spotify_services.get_user_playlist_order', return_value=['pC', 'pA', 'pB'])
    
    sorted_playlists = get_user_playlists(mock_sp)
    
    assert len(sorted_playlists) == 3
    assert sorted_playlists[0]['id'] == 'pC'
    assert sorted_playlists[1]['id'] == 'pA'
    assert sorted_playlists[2]['id'] == 'pB'

def test_get_user_playlists_with_deleted_playlist(mocker):
    """
    Test that the sorting logic gracefully handles when a playlist in the custom order
    has been deleted from Spotify.
    """
    mock_sp = MagicMock()
    # Spotify only returns playlists A and C
    mock_sp.current_user_playlists.return_value = {
        "items": [
            {"id": "pA", "name": "Playlist A", "images": [], "owner": {"display_name": "user"}, "tracks": {"total": 1}},
            {"id": "pC", "name": "Playlist C", "images": [], "owner": {"display_name": "user"}, "tracks": {"total": 1}},
        ],
        "next": None
    }
    
    # The custom order still contains the deleted playlist B
    mocker.patch('src.services.spotify_services.get_user_playlist_order', return_value=['pC', 'pB', 'pA'])
    
    sorted_playlists = get_user_playlists(mock_sp)
    
    # The final list should not contain the deleted playlist and should not crash
    assert len(sorted_playlists) == 2
    assert sorted_playlists[0]['id'] == 'pC'
    assert sorted_playlists[1]['id'] == 'pA'