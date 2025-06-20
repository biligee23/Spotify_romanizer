"""
tests/services/test_text_processors.py - Unit tests for text processing functions.
"""

from src.utils.text_processors import clean_genius_metadata, romanize_lyrics, format_processed_text

def test_clean_genius_metadata():
    """
    Test the cleaning of boilerplate text from Genius lyrics.
    """
    # Use a more realistic input that matches the regex pattern
    raw_lyrics = "1 Contributor\nTrack Name Lyrics[Verse 1]\nHello world\nYou might also like\n123Embed"
    cleaned = clean_genius_metadata(raw_lyrics)
    assert "Contributor" not in cleaned
    assert "Lyrics[Verse 1]" not in cleaned # The regex removes the header up to the word "Lyrics"
    assert "You might also like" not in cleaned
    assert "Embed" not in cleaned
    assert cleaned == "Hello world"

def test_format_processed_text():
    """
    Test the final formatting of text (capitalization, spacing).
    """
    raw_text = "  hello   world\n\nthis is a test  "
    formatted = format_processed_text(raw_text)
    assert formatted == "Hello world\n\nThis is a test"

def test_romanize_lyrics_simple():
    """
    Test basic romanization of Japanese text.
    """
    japanese_text = "こんにちは"
    romanized = romanize_lyrics(japanese_text)
    assert romanized == "Konnichiha"