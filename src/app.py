"""
Application Module

This module initializes and configures the Flask application, including caching,
Spotify OAuth, Celery, and other extensions. It also registers blueprints.
"""

# Standard library imports
import logging

# Third-party imports
from flask import Flask, session
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth

# Local application imports
from src.config import Config
from src.extensions import cache, celery_app
from src.routes import main_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """
    Create and configure the Flask application.

    This function initializes the Flask app, loads configuration settings, sets up
    extensions (cache, Spotify OAuth, Celery), and registers blueprints.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # Load configuration
    app.config.from_object(Config)
    logger.info("Configuration loaded successfully.")
    Config.validate_env_vars()

    # Configure cache
    cache_config = Config.get_cache_config()
    cache.init_app(app, config=cache_config)
    logger.info("Cache initialized with config: %s", cache_config)

    # Configure Celery
    celery_app.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery_app.set_default()
    app.celery = celery_app
    logger.info("Celery configured for the application.")

    # Initialize Spotify OAuth within app context
    with app.app_context():
        cache_handler = FlaskSessionCacheHandler(session)
        sp_oauth = SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=Config.SPOTIFY_REDIRECT_URI,
            scope=Config.SPOTIFY_SCOPE,
            cache_handler=cache_handler,
            show_dialog=True,
        )
        app.sp_oauth = sp_oauth
        app.cache_handler = cache_handler
        logger.info("Spotify OAuth and cache handler initialized.")

    # Register blueprints
    app.register_blueprint(main_bp)
    logger.info("Blueprint '%s' registered.", main_bp.name)

    return app


if __name__ == "__main__":
    app_instance = create_app()
    debug_mode = not Config.is_production()
    logger.info(
        "Running application in %s mode.",
        "production" if Config.is_production() else "development",
    )
    app_instance.run(debug=debug_mode, host="0.0.0.0")