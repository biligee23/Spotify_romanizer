"""
Configuration module for the application.
This module loads environment variables and defines the application's configuration settings.
"""

# Standard library imports
import os

# Third-party imports
from dotenv import load_dotenv

load_dotenv()  # Load environment variables


class Config:
    """
    Configuration class for the application.
    """

    # General Configuration
    SECRET_KEY = os.urandom(64)

    # Cache Configuration
    CACHE_TYPE = os.getenv("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL", "redis://redis:6379/0")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "10800"))
    CACHE_KEY_PREFIX = os.getenv("CACHE_KEY_PREFIX", "lyrics_")
    CACHE_REDIS_HOST = os.getenv("CACHE_REDIS_HOST", "redis")
    CACHE_REDIS_PORT = int(os.getenv("CACHE_REDIS_PORT", "6379"))
    CACHE_OPTIONS = {
        "CLIENT_CLASS": os.getenv("CACHE_OPTIONS_CLIENT_CLASS", "redis.Redis"),
        "REDIS_MAX_CONNECTIONS": int(os.getenv("CACHE_OPTIONS_REDIS_MAX_CONNECTIONS", "20")),
        "MAX_ENTRIES": int(os.getenv("CACHE_OPTIONS_MAX_ENTRIES", "100")),
    }

    # API Keys
    GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    # Spotify OAuth Configuration
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:5000/callback")
    SPOTIFY_SCOPE = (
        "playlist-read-private user-library-read "
        "user-read-playback-state user-modify-playback-state app-remote-control "
        "playlist-modify-public playlist-modify-private"
    )
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

    # Application Constants
    FALLBACK_YOUTUBE_URL = "https://www.youtube.com/embed/dQw4w9WgXcQ"

    # Validate essential environment variables
    REQUIRED_ENV_VARS = [
        "GENIUS_ACCESS_TOKEN",
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "YOUTUBE_API_KEY",
    ]

    @staticmethod
    def validate_env_vars():
        """
        Validates that all required environment variables are set.
        """
        missing = [var for var in Config.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    @classmethod
    def is_production(cls) -> bool:
        """
        Determines if the application is running in production mode.
        """
        return os.getenv("FLASK_ENV", "development").lower() == "production"

    @classmethod
    def get_cache_config(cls) -> dict:
        """
        Retrieves the complete cache configuration as a dictionary.
        """
        return {
            "CACHE_TYPE": cls.CACHE_TYPE,
            "CACHE_REDIS_URL": cls.CACHE_REDIS_URL,
            "CACHE_DEFAULT_TIMEOUT": cls.CACHE_DEFAULT_TIMEOUT,
            "CACHE_KEY_PREFIX": cls.CACHE_KEY_PREFIX,
            "CACHE_REDIS_HOST": cls.CACHE_REDIS_HOST,
            "CACHE_REDIS_PORT": cls.CACHE_REDIS_PORT,
            "CACHE_OPTIONS": cls.CACHE_OPTIONS,
        }