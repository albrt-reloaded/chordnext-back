"""Verificación de Google ID tokens (Sign-in with Google).

El cliente obtiene un `id_token` mediante expo-auth-session y lo envía aquí.
Verificamos la firma contra los certificados públicos de Google y comprobamos
que el `aud` coincida con nuestro Client ID.
"""

from __future__ import annotations

from flask import current_app
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


class GoogleAuthError(Exception):
    pass


def verify_google_id_token(token: str) -> dict:
    """Devuelve el payload del id_token o lanza GoogleAuthError."""
    audiences = current_app.config.get("GOOGLE_CLIENT_IDS") or []
    if not audiences:
        raise GoogleAuthError("GOOGLE_CLIENT_ID no está configurado en el servidor")

    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audiences,
            clock_skew_in_seconds=10,
        )
    except ValueError as exc:  # firma inválida, aud incorrecto, expirado...
        raise GoogleAuthError(str(exc)) from exc

    if payload.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleAuthError("Emisor de token no válido")

    return payload
