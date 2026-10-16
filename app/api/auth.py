"""Autenticación: Email/Password + Google OAuth2 + JWT."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import func, select

from ..extensions import db
from ..models import User
from ..schemas import GoogleAuthSchema, LoginSchema, RegisterSchema, UpdateProfileSchema
from ..utils.google import GoogleAuthError, verify_google_id_token
from ._common import current_user, load, login_required

auth_bp = Blueprint("auth", __name__)


def _serialize(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatarUrl": user.avatar_url,
        "provider": user.provider,
        "preferredKey": user.preferred_key,
        "theme": user.theme,
        "fontSize": user.font_size,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
    }


def _issue_tokens(user: User) -> dict:
    identity = str(user.id)
    return {
        "accessToken": create_access_token(identity=identity),
        "refreshToken": create_refresh_token(identity=identity),
        "user": _serialize(user),
    }


def _find_by_email(email: str) -> User | None:
    return db.session.scalar(select(User).where(func.lower(User.email) == email.lower()))


@auth_bp.post("/register")
def register():
    data = load(RegisterSchema(), request.get_json(silent=True) or {})
    if _find_by_email(data["email"]):
        return jsonify({"message": "El email ya está registrado"}), 409

    user = User(
        email=data["email"].lower(),
        name=data.get("name") or data["email"].split("@")[0],
        provider="local",
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify(_issue_tokens(user)), 201


@auth_bp.post("/login")
def login():
    data = load(LoginSchema(), request.get_json(silent=True) or {})
    user = _find_by_email(data["email"])
    if user is None or not user.check_password(data["password"]):
        return jsonify({"message": "Credenciales inválidas"}), 401
    return jsonify(_issue_tokens(user)), 200


@auth_bp.post("/google")
def google_login():
    data = load(GoogleAuthSchema(), request.get_json(silent=True) or {})
    try:
        payload = verify_google_id_token(data["idToken"])
    except GoogleAuthError as exc:
        return jsonify({"message": "Token de Google inválido", "detail": str(exc)}), 401

    email = payload.get("email")
    google_id = payload.get("sub")
    if not email or not payload.get("email_verified", True):
        return jsonify({"message": "Cuenta de Google sin email verificado"}), 400

    user = db.session.scalar(select(User).where(User.google_id == google_id)) or _find_by_email(email)
    if user is None:
        user = User(
            email=email.lower(),
            name=payload.get("name") or data.get("name") or email.split("@")[0],
            avatar_url=payload.get("picture") or data.get("avatarUrl"),
            provider="google",
            google_id=google_id,
        )
        db.session.add(user)
    else:
        # Vincula la cuenta de Google a un usuario existente y refresca el perfil.
        user.google_id = user.google_id or google_id
        user.provider = "google" if user.provider == "local" and not user.password_hash else user.provider
        user.avatar_url = payload.get("picture") or user.avatar_url
        user.name = user.name or payload.get("name", "")
    db.session.commit()
    return jsonify(_issue_tokens(user)), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user = db.session.get(User, get_jwt_identity())
    if user is None or user.deleted:
        return jsonify({"message": "Usuario no encontrado"}), 404
    return jsonify({"accessToken": create_access_token(identity=str(user.id))}), 200


@auth_bp.get("/me")
@login_required
def me(user: User):
    return jsonify(_serialize(user)), 200


@auth_bp.patch("/me")
@login_required
def update_me(user: User):
    data = load(UpdateProfileSchema(), request.get_json(silent=True) or {}, partial=True)
    if "name" in data:
        user.name = data["name"]
    if "avatarUrl" in data:
        user.avatar_url = data["avatarUrl"]
    if "preferredKey" in data:
        user.preferred_key = data["preferredKey"]
    if "theme" in data:
        user.theme = data["theme"]
    if "fontSize" in data:
        user.font_size = data["fontSize"]
    user.touch()
    db.session.commit()
    return jsonify(_serialize(user)), 200
