"""Blueprints de la API."""

from .auth import auth_bp
from .songs import songs_bp
from .setlists import setlists_bp
from .tags import tags_bp
from .progressions import progressions_bp
from .sync import sync_bp

__all__ = ["auth_bp", "songs_bp", "setlists_bp", "tags_bp", "progressions_bp", "sync_bp"]
