"""
tests/tasks/test_celery_tasks.py - Unit tests for Celery task logic.
"""

from unittest.mock import MagicMock

from src.celery_worker import fetch_and_populate_task, translate_and_update_cache_task

def test_fetch_and_populate_task(app, mocker):
    """
    Test the main content fetching task within a real app context.
    """
    with app.app_context():
        mock_cache = mocker.patch('src.extensions.cache')
        mock_genius_client = MagicMock()
        mock_genius_client.search_songs.return_value = {
            "hits": [{"result": {"id": 123, "title": "Test Song", "primary_artist": {"name": "Test Artist"}}}]
        }
        mock_genius_client.lyrics.return_value = "こんにちは"
        mocker.patch('src.services.genius_services.get_genius_client', return_value=mock_genius_client)
        
        mocker.patch('src.services.youtube_services.search_youtube_video', return_value="http://youtube.com/test")
        mock_translate_task = mocker.patch('src.celery_worker.translate_and_update_cache_task.delay')
        mocker.patch('src.utils.cache_manager.lfu_cache_manager')

        mock_cache.get.return_value = {"song_title": "Test Song"}

        fetch_and_populate_task(None, "track1", "Test Song", "Test Artist")

        mock_translate_task.assert_called_once_with("track1", "こんにちは")
        
        updated_content = mock_cache.set.call_args[0][1]
        assert updated_content['original_lyrics'] == "こんにちは"
        assert "Konnichiha" in updated_content['romanized_lyrics']

def test_translate_task(app, mocker):
    """
    Test the translation sub-task's success path.
    """
    with app.app_context():
        mock_cache = mocker.patch('src.extensions.cache')
        mock_translator = mocker.patch('src.celery_worker.GoogleTranslator')
        
        mock_translator.return_value.translate.return_value = "Hello world"
        mock_cache.get.return_value = {"original_lyrics": "こんにちは"}

        translate_and_update_cache_task("track1", "こんにちは")

        updated_content = mock_cache.set.call_args[0][1]
        assert updated_content['translated_lyrics'] == "Hello world"

def test_translate_task_failure(app, mocker):
    """
    Test that the translation task correctly handles an exception from the translator.
    """
    with app.app_context():
        mock_cache = mocker.patch('src.extensions.cache')
        mock_translator = mocker.patch('src.celery_worker.GoogleTranslator')
        
        # Simulate the translator raising an exception
        mock_translator.return_value.translate.side_effect = Exception("API limit reached")
        mock_cache.get.return_value = {"original_lyrics": "こんにちは"}

        translate_and_update_cache_task("track1", "こんにちは")

        # Assert that the cache was updated with a 'failed' status
        updated_content = mock_cache.set.call_args[0][1]
        assert updated_content['translated_lyrics'] == "Translation failed."