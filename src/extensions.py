"""
Extensions Module

This module initializes and configures Flask extensions, external libraries, and global objects
used throughout the application. It includes configurations for Flask-Caching,
Pykakasi (for Romanization), and SudachiPy (for tokenization).
"""

# Third-party imports
import pykakasi
from celery import Celery
from flask_caching import Cache
from sudachipy import dictionary

# Initialize Flask extensions
cache = Cache()
celery_app = Celery(__name__)

# Initialize Pykakasi for Romanization
_kks = pykakasi.kakasi()
_kks.setMode("H", "a")
_kks.setMode("K", "a")
_kks.setMode("J", "a")
_kks.setMode("s", True)
_kks.setMode("C", True)
KKS_CONVERTER = _kks.getConverter()

# Initialize SudachiPy for tokenization
TOKENIZER_OBJ = dictionary.Dictionary().create()

# Placeholders for Spotify OAuth and cache handler
SP_OAUTH = None
CACHE_HANDLER = None