"""Helpers compartidos por los blueprints."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import abort, g, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from marshmallow import Schema, ValidationError

from ..extensions import db
from ..models import User


def load(schema: Schema, payload: dict, partial: bool = False) -> dict:
    """Valida `payload` contra `schema` o aborta con 422."""
    try:
        return schema.load(payload or {}, partial=partial)
    except ValidationError as err:
        abort(422, description=str(err.messages))


def current_user() -> User:
    if "current_user" in g:
        return g.current_user
    user = db.session.get(User, get_jwt_identity())
    if user is None or user.deleted:
        abort(404, description="Usuario no encontrado")
    g.current_user = user
    return user


def login_required(fn: Callable) -> Callable:
    """Exige JWT válido e inyecta el usuario en `g.current_user`."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        verify_jwt_in_request()
        user = current_user()
        return fn(*args, user=user, **kwargs)

    return wrapper


def unprocessable(errors: Any):
    return jsonify({"message": "Datos inválidos", "errors": errors}), 422
