"""Schemas Marshmallow para validación de entrada/salida."""

from .auth import GoogleAuthSchema, LoginSchema, RegisterSchema, UpdateProfileSchema
from .song import SongSchema, SongSearchSchema
from .setlist import SetlistSchema
from .tag import TagSchema
from .progression import ProgressionSchema
from .sync import SyncPushSchema

__all__ = [
    "GoogleAuthSchema",
    "LoginSchema",
    "RegisterSchema",
    "UpdateProfileSchema",
    "SongSchema",
    "SongSearchSchema",
    "SetlistSchema",
    "TagSchema",
    "ProgressionSchema",
    "SyncPushSchema",
]
