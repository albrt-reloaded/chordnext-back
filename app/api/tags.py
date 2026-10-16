"""CRUD de etiquetas."""

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from ..extensions import db
from ..models import Tag
from ..schemas import TagSchema
from ._common import load, login_required

tags_bp = Blueprint("tags", __name__)


def _owned(user, tag_id: str) -> Tag | None:
    return db.session.scalar(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id, Tag.deleted.is_(False))
    )


@tags_bp.get("")
@login_required
def list_tags(user):
    rows = db.session.scalars(
        select(Tag).where(Tag.user_id == user.id, Tag.deleted.is_(False)).order_by(Tag.name)
    ).all()
    return jsonify({"items": [t.to_dict() for t in rows]}), 200


@tags_bp.post("")
@login_required
def create_tag(user):
    data = load(TagSchema(), request.get_json(silent=True) or {})
    existing = db.session.scalar(
        select(Tag).where(Tag.user_id == user.id, func.lower(Tag.name) == data["name"].lower())
    )
    if existing:
        if existing.deleted:
            existing.deleted = False
            existing.touch()
            db.session.commit()
        return jsonify({"id": existing.id, "name": existing.name, "color": existing.color}), 200
    tag = Tag(user_id=user.id, name=data["name"], color=data["color"])
    db.session.add(tag)
    db.session.commit()
    return jsonify({"id": tag.id, "name": tag.name, "color": tag.color}), 201


@tags_bp.patch("/<tag_id>")
@tags_bp.put("/<tag_id>")
@login_required
def update_tag(user, tag_id: str):
    tag = _owned(user, tag_id)
    if tag is None:
        return jsonify({"message": "Etiqueta no encontrada"}), 404
    data = load(TagSchema(), request.get_json(silent=True) or {}, partial=True)
    if "name" in data:
        tag.name = data["name"]
    if "color" in data:
        tag.color = data["color"]
    tag.touch()
    db.session.commit()
    return jsonify({"id": tag.id, "name": tag.name, "color": tag.color}), 200


@tags_bp.delete("/<tag_id>")
@login_required
def delete_tag(user, tag_id: str):
    tag = _owned(user, tag_id)
    if tag is None:
        return jsonify({"message": "Etiqueta no encontrada"}), 404
    tag.deleted = True
    tag.touch()
    db.session.commit()
    return "", 204
