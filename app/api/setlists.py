"""CRUD de cancioneros (setlists), gestión de items y reordenamiento."""

from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields
from sqlalchemy import select

from ..extensions import db
from ..models import Setlist, SetlistItem, Song
from ..schemas import SetlistSchema
from ._common import load, login_required

setlists_bp = Blueprint("setlists", __name__)


class AddSongSchema(Schema):
    songId = fields.String(required=True)
    keyOverride = fields.String(load_default=None, allow_none=True)
    notes = fields.String(load_default="")


class ReorderSchema(Schema):
    itemIds = fields.List(fields.String(), load_default=list)
    songIds = fields.List(fields.String(), load_default=list)


def _owned(user, setlist_id: str) -> Setlist | None:
    return db.session.scalar(
        select(Setlist).where(
            Setlist.id == setlist_id, Setlist.user_id == user.id, Setlist.deleted.is_(False)
        )
    )


def _apply_items(setlist: Setlist, items: list[dict]) -> None:
    """Reemplaza los items del setlist preservando el orden enviado."""
    setlist.items.clear()
    db.session.flush()
    for index, raw in enumerate(items):
        song_id = raw.get("songId") or raw.get("song_id")
        if not song_id:
            continue
        setlist.items.append(
            SetlistItem(
                song_id=song_id,
                position=raw.get("position", index),
                key_override=raw.get("keyOverride") or raw.get("key_override"),
                notes=raw.get("notes", ""),
            )
        )


@setlists_bp.get("")
@login_required
def list_setlists(user):
    rows = db.session.scalars(
        select(Setlist)
        .where(Setlist.user_id == user.id, Setlist.deleted.is_(False))
        .order_by(Setlist.updated_at.desc())
    ).all()
    return jsonify({"items": [s.to_dict() for s in rows]}), 200


@setlists_bp.post("")
@login_required
def create_setlist(user):
    data = load(SetlistSchema(), request.get_json(silent=True) or {})
    setlist = Setlist(user_id=user.id, name=data["name"], description=data.get("description", ""))
    db.session.add(setlist)
    db.session.flush()
    if data.get("items"):
        _apply_items(setlist, data["items"])
    db.session.commit()
    return jsonify(setlist.to_dict()), 201


@setlists_bp.get("/<setlist_id>")
@login_required
def get_setlist(user, setlist_id: str):
    setlist = _owned(user, setlist_id)
    if setlist is None:
        return jsonify({"message": "Cancionero no encontrado"}), 404
    return jsonify(setlist.to_dict()), 200


@setlists_bp.put("/<setlist_id>")
@setlists_bp.patch("/<setlist_id>")
@login_required
def update_setlist(user, setlist_id: str):
    setlist = _owned(user, setlist_id)
    if setlist is None:
        return jsonify({"message": "Cancionero no encontrado"}), 404
    data = load(SetlistSchema(), request.get_json(silent=True) or {}, partial=True)
    if "name" in data:
        setlist.name = data["name"]
    if "description" in data:
        setlist.description = data["description"]
    if data.get("items") is not None:
        _apply_items(setlist, data["items"])
    setlist.touch()
    db.session.commit()
    return jsonify(setlist.to_dict()), 200


@setlists_bp.delete("/<setlist_id>")
@login_required
def delete_setlist(user, setlist_id: str):
    setlist = _owned(user, setlist_id)
    if setlist is None:
        return jsonify({"message": "Cancionero no encontrado"}), 404
    setlist.deleted = True
    setlist.touch()
    db.session.commit()
    return "", 204


@setlists_bp.post("/<setlist_id>/songs")
@login_required
def add_song(user, setlist_id: str):
    setlist = _owned(user, setlist_id)
    if setlist is None:
        return jsonify({"message": "Cancionero no encontrado"}), 404
    data = load(AddSongSchema(), request.get_json(silent=True) or {})

    song = db.session.scalar(
        select(Song).where(Song.id == data["songId"], Song.user_id == user.id, Song.deleted.is_(False))
    )
    if song is None:
        return jsonify({"message": "Canción no encontrada"}), 404

    position = max((i.position for i in setlist.items), default=-1) + 1
    item = SetlistItem(
        setlist_id=setlist.id,
        song_id=song.id,
        position=position,
        key_override=data.get("keyOverride"),
        notes=data.get("notes", ""),
    )
    db.session.add(item)
    setlist.touch()
    db.session.commit()
    return jsonify(setlist.to_dict()), 201


@setlists_bp.delete("/<setlist_id>/songs/<item_id>")
@login_required
def remove_song(user, setlist_id: str, item_id: str):
    setlist = _owned(user, setlist_id)
    if setlist is None:
        return jsonify({"message": "Cancionero no encontrado"}), 404
    item = next((i for i in setlist.items if i.id == item_id), None)
    if item is None:
        return jsonify({"message": "Item no encontrado"}), 404
    db.session.delete(item)
    _reindex(setlist)
    setlist.touch()
    db.session.commit()
    return jsonify(setlist.to_dict()), 200


@setlists_bp.post("/<setlist_id>/reorder")
@login_required
def reorder(user, setlist_id: str):
    setlist = _owned(user, setlist_id)
    if setlist is None:
        return jsonify({"message": "Cancionero no encontrado"}), 404
    data = load(ReorderSchema(), request.get_json(silent=True) or {})

    if data.get("itemIds"):
        order = {item_id: i for i, item_id in enumerate(data["itemIds"])}
        for item in setlist.items:
            if item.id in order:
                item.position = order[item.id]
    elif data.get("songIds"):
        order = {sid: i for i, sid in enumerate(data["songIds"])}
        for item in setlist.items:
            if item.song_id in order:
                item.position = order[item.song_id]

    setlist.touch()
    db.session.commit()
    setlist.items.sort(key=lambda i: i.position)
    return jsonify(setlist.to_dict()), 200


def _reindex(setlist: Setlist) -> None:
    remaining = sorted(setlist.items, key=lambda i: i.position)
    for index, item in enumerate(remaining):
        item.position = index
