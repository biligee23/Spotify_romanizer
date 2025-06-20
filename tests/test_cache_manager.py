"""
tests/services/test_cache_manager.py - Unit tests for the LFUCacheManager.
"""

from unittest.mock import MagicMock, patch

from src.utils.cache_manager import LFUCacheManager

def test_lfu_eviction_logic(mocker):
    """
    Test that the LFU eviction correctly removes the least frequently used,
    non-favorite item when the cache is full.
    """
    # Mock the dependencies of the cache manager
    mock_redis = MagicMock()
    mocker.patch('src.utils.cache_manager.redis.Redis', return_value=mock_redis)
    mocker.patch('src.utils.cache_manager.cache')

    # Initialize the manager with a small size for easy testing
    cache_manager = LFUCacheManager(max_entries=3)
    cache_manager.redis = mock_redis

    # --- Setup the cache state ---
    # 1. The user's favorites list contains 'track_F'
    mock_redis.smembers.return_value = {'track_F'}
    
    # 2. Configure the mock for two separate calls to zrange
    # The first call gets ALL keys to calculate size.
    # The second call gets the LEAST USED keys for potential eviction.
    mock_redis.zrange.side_effect = [
        ['track_A', 'track_B', 'track_C', 'track_F'], # First call result
        ['track_C', 'track_A', 'track_B']             # Second call result
    ]
    
    # 3. Mock the delete method itself to make the assertion clean and robust
    mock_delete = mocker.patch.object(cache_manager, 'delete')

    # --- Trigger the eviction ---
    # Add a new item, which should cause an eviction because there are 3 non-favorites
    cache_manager.set('track_D', {'data': 'new'})

    # --- Assertions ---
    # The loop inside set() will check potential evictees:
    # 1. It gets 'track_C'. It checks if it's a favorite. It's not.
    # 2. It calls delete('track_C') and breaks the loop.
    mock_delete.assert_called_once_with('track_C')