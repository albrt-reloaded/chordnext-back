"""Sincronización offline-first (push/pull) con resolución last-write-wins.

Estrategia:
  * El cliente hace PULL incremental desde su último `since`.
  * El cliente hace PUSH de los registros modificados localmente.
  * El servidor aplica cada registro si su `updatedAt` es >= al remoto.
  * Los borrados se propagan con `deleted = true` (soft-delete).
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from ..extensions import db
from ..models import Progression, Setlist, SetlistItem, Song, Tag
from ..schemas import SyncPushSchema
from ._common import load, login_required

sync_bp = Blueprint("sync", __name__)


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _incoming_wins(incoming_dt: datetime | None, current_dt: datetime | None) -> bool:
    if incoming_dt is None:
        return False
    if current_dt is None:
        return True
    if current_dt.tzinfo is None:
        current_dt = current_dt.replace(tzinfo=timezone.utc)
    return incoming_dt >= current_dt


# --------------------------------------------------------------------------- #
# PULL
# --------------------------------------------------------------------------- #
@sync_bp.get("/pull")
@login_required
def pull(user):
    since = _parse_dt(request.args.get("since")) or datetime(1970, 1, 1, tzinfo=timezone.utc)

    songs = db.session.scalars(
        select(Song).where(Song.user_id == user.id, Song.updated_at > since)
    ).unique().all()
    setlists = db.session.scalars(
        select(Setlist).where(Setlist.user_id == user.id, Setlist.updated_at > since)
    ).unique().all()
    tags = db.session.scalars(
        select(Tag).where(Tag.user_id == user.id, Tag.updated_at > since)
    ).all()
    progressions = db.session.scalars(
        select(Progression).where(Progression.user_id == user.id, Progression.updated_at > since)
    ).all()

    return jsonify(
        {
            "serverTime": datetime.now(timezone.utc).isoformat(),
            "songs": [_song_out(s) for s in songs],
            "setlists": [s.to_dict() for s in setlists],
            "tags": [t.to_dict() for t in tags],
            "progressions": [p.to_dict() for p in progressions],
        }
    ), 200


def _song_out(song: Song) -> dict:
    data = song.to_dict()
    data["tagIds"] = [t.id for t in song.tags]
    return data


# --------------------------------------------------------------------------- #
# PUSH
# --------------------------------------------------------------------------- #
@sync_bp.post("/push")
@login_required
def push(user):
    payload = load(SyncPushSchema(), request.get_json(silent=True) or {})
    results = {"songs": [], "setlists": [], "tags": [], "progressions": []}

    for raw in payload["tags"]:
        results["tags"].append(_push_tag(user, raw))
    db.session.flush()
    for raw in payload["songs"]:
        results["songs"].append(_push_song(user, raw))
    for raw in payload["setlists"]:
        results["setlists"].append(_push_setlist(user, raw))
    for raw in payload["progressions"]:
        results["progressions"].append(_push_progression(user, raw))

    db.session.commit()
    return jsonify(
        {"serverTime": datetime.now(timezone.utc).isoformat(), "results": results}
    ), 200


def _status(record_id: str, action: str, obj=None) -> dict:
    return {"id": record_id, "action": action, "serverUpdatedAt": getattr(obj, "updated_at", None).isoformat() if obj is not None and obj.updated_at else None}


def _push_tag(user, raw: dict) -> dict:
    tag = db.session.scalar(select(Tag).where(Tag.id == raw.get("id"), Tag.user_id == user.id))
    incoming = _parse_dt(raw.get("updatedAt"))
    if tag is None:
        tag = Tag(
            id=raw.get("id") or None,
            user_id=user.id,
            name=raw.get("name", "etiqueta"),
            color=raw.get("color", "#6366f1"),
            deleted=bool(raw.get("deleted", False)),
        )
        db.session.add(tag)
        db.session.flush()
        return _status(tag.id, "created", tag)
    if _incoming_wins(incoming, tag.updated_at):
        tag.name = raw.get("name", tag.name)
        tag.color = raw.get("color", tag.color)
        tag.deleted = bool(raw.get("deleted", tag.deleted))
        tag.touch()
        return _status(tag.id, "updated", tag)
    return _status(tag.id, "skipped", tag)


def _push_song(user, raw: dict) -> dict:
    song = db.session.scalar(select(Song).where(Song.id == raw.get("id"), Song.user_id == user.id))
    incoming = _parse_dt(raw.get("updatedAt"))
    if song is None:
        song = Song(id=raw.get("id") or None, user_id=user.id)
        db.session.add(song)
    elif not _incoming_wins(incoming, song.updated_at):
        return _status(song.id, "skipped", song)

    song.title = raw.get("title", song.title or "")
    song.artist = raw.get("artist", getattr(song, "artist", "") or "")
    song.key = raw.get("key", song.key or "C")
    song.capo = raw.get("capo", song.capo or 0)
    song.bpm = raw.get("bpm", song.bpm or 90)
    song.time_signature = raw.get("timeSignature", song.time_signature or "4/4")
    song.content = raw.get("content", song.content or "")
    song.content_json = raw.get("contentJson", song.content_json)
    song.has_chords = raw.get("hasChords", song.has_chords if song.has_chords is not None else True)
    song.notes = raw.get("notes", song.notes or "")
    song.deleted = bool(raw.get("deleted", getattr(song, "deleted", False)))

    tag_ids = raw.get("tagIds") or []
    if tag_ids:
        song.tags = db.session.scalars(
            select(Tag).where(Tag.user_id == user.id, Tag.id.in_(tag_ids))
        ).all()

    if incoming:
        song.updated_at = incoming
    song.revision = (song.revision or 0) + 1
    db.session.flush()
    return _status(song.id, "upserted", song)


def _push_setlist(user, raw: dict) -> dict:
    setlist = db.session.scalar(
        select(Setlist).where(Setlist.id == raw.get("id"), Setlist.user_id == user.id)
    )
    incoming = _parse_dt(raw.get("updatedAt"))
    if setlist is None:
        setlist = Setlist(id=raw.get("id") or None, user_id=user.id)
        db.session.add(setlist)
    elif not _incoming_wins(incoming, setlist.updated_at):
        return _status(setlist.id, "skipped", setlist)

    setlist.name = raw.get("name", setlist.name or "")
    setlist.description = raw.get("description", setlist.description or "")
    setlist.deleted = bool(raw.get("deleted", getattr(setlist, "deleted", False)))

    items = raw.get("items")
    if items is not None and not setlist.deleted:
        setlist.items.clear()
        db.session.flush()
        for index, item in enumerate(items):
            song_id = item.get("songId") or item.get("song_id")
            if not song_id:
                continue
            setlist.items.append(
                SetlistItem(
                    song_id=song_id,
                    position=item.get("position", index),
                    key_override=item.get("keyOverride") or item.get("key_override"),
                    notes=item.get("notes", ""),
                )
            )

    if incoming:
        setlist.updated_at = incoming
    setlist.revision = (setlist.revision or 0) + 1
    db.session.flush()
    return _status(setlist.id, "upserted", setlist)


def _push_progression(user, raw: dict) -> dict:
    prog = db.session.scalar(
        select(Progression).where(Progression.id == raw.get("id"), Progression.user_id == user.id)
    )
    incoming = _parse_dt(raw.get("updatedAt"))
    if prog is None:
        prog = Progression(id=raw.get("id") or None, user_id=user.id)
        db.session.add(prog)
    elif not _incoming_wins(incoming, prog.updated_at):
        return _status(prog.id, "skipped", prog)

    prog.name = raw.get("name", prog.name or "")
    prog.degrees = raw.get("degrees", prog.degrees or "")
    prog.key = raw.get("key", prog.key or "C")
    prog.preferred = bool(raw.get("preferred", getattr(prog, "preferred", False)))
    prog.deleted = bool(raw.get("deleted", getattr(prog, "deleted", False)))
    if incoming:
        prog.updated_at = incoming
    prog.revision = (prog.revision or 0) + 1
    db.session.flush()
    return _status(prog.id, "upserted", prog)
