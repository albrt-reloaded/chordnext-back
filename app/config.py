"""Configuración de la aplicación ChordNext.

Todas las variables se leen del entorno (`.env` en desarrollo).
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url: str | None) -> str:
    """Supabase entrega URLs `postgres://` que SQLAlchemy 2.x ya no acepta."""
    if not url:
        return "sqlite:///chordnext.db"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # --- Base de datos ---
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_HOURS", "1")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "30")))
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ERROR_MESSAGE_KEY = "message"

    # --- Google OAuth2 ---
    # Puede ser uno o varios Client IDs separados por coma (web, android, ios).
    # El backend valida el `aud` del id_token contra esta lista.
    _google_ids = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_IDS = [c.strip() for c in _google_ids.split(",") if c.strip()]
    GOOGLE_CLIENT_ID = GOOGLE_CLIENT_IDS[0] if GOOGLE_CLIENT_IDS else None
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # --- CORS ---
    _origins = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS = "*" if _origins.strip() == "*" else [o.strip() for o in _origins.split(",") if o.strip()]

    JSON_SORT_KEYS = False
