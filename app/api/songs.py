"""CRUD de canciones + búsqueda y filtros avanzados."""

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_, select

from ..extensions import db
from ..models import Song, Tag
from ..schemas import SongSchema, SongSearchSchema
from ._common import load, login_required

songs_bp = Blueprint("songs", __name__)


def _resolve_tags(user, tag_ids: list[str], tag_names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    if tag_ids:
        tags.extend(
            db.session.scalars(
                select(Tag).where(Tag.user_id == user.id, Tag.id.in_(tag_ids), Tag.deleted.is_(False))
            ).all()
        )
    for name in tag_names or []:
        clean = name.strip()
        if not clean:
            continue
        existing = db.session.scalar(
            select(Tag).where(Tag.user_id == user.id, func.lower(Tag.name) == clean.lower())
        )
        if existing is None:
            existing = Tag(user_id=user.id, name=clean)
            db.session.add(existing)
            db.session.flush()
        tags.append(existing)
    # deduplica preservando orden
    seen, unique = set(), []
    for tag in tags:
        if tag.id not in seen:
            seen.add(tag.id)
            unique.append(tag)
    return unique


@songs_bp.get("")
@login_required
def list_songs(user):
    filters = load(SongSearchSchema(), request.args.to_dict(), partial=True)
    stmt = select(Song).where(Song.user_id == user.id, Song.deleted.is_(False))

    q = (filters.get("q") or "").strip()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Song.title.ilike(like), Song.artist.ilike(like)))
    if filters.get("key"):
        stmt = stmt.where(Song.key == filters["key"])
    if filters.get("artist"):
        stmt = stmt.where(Song.artist.ilike(f"%{filters['artist']}%"))
    if filters.get("bpmMin") is not None:
        stmt = stmt.where(Song.bpm >= filters["bpmMin"])
    if filters.get("bpmMax") is not None:
        stmt = stmt.where(Song.bpm <= filters["bpmMax"])
    if filters.get("hasChords") is not None:
        stmt = stmt.where(Song.has_chords.is_(filters["hasChords"]))
    if filters.get("tags"):
        names = [t.lower() for t in filters["tags"]]
        stmt = stmt.where(Song.tags.any(func.lower(Tag.name).in_(names)))

    sort_col = {
        "updatedAt": Song.updated_at,
        "createdAt": Song.created_at,
        "title": Song.title,
        "artist": Song.artist,
        "bpm": Song.bpm,
    }[filters.get("sort", "updatedAt")]
    stmt = stmt.order_by(sort_col.asc() if filters.get("order") == "asc" else sort_col.desc())

    limit = filters.get("limit", 50)
    offset = filters.get("offset", 0)
    total = db.session.scalar(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    )
    rows = db.session.scalars(stmt.limit(limit).offset(offset)).unique().all()

    return jsonify(
        {
            "items": [s.to_dict() for s in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    ), 200


@songs_bp.post("")
@login_required
def create_song(user):
    data = load(SongSchema(), request.get_json(silent=True) or {})
    tags = _resolve_tags(user, data.pop("tagIds", []), data.pop("tagNames", []))
    song = Song(
        user_id=user.id,
        title=data["title"],
        artist=data["artist"],
        key=data["key"],
        capo=data["capo"],
        bpm=data["bpm"],
        time_signature=data["timeSignature"],
        content=data["content"],
        content_json=data["contentJson"],
        has_chords=data["hasChords"],
        notes=data["notes"],
        tags=tags,
    )
    db.session.add(song)
    db.session.commit()
    return jsonify(song.to_dict()), 201


def _owned_song(user, song_id: str) -> Song | None:
    return db.session.scalar(
        select(Song).where(Song.id == song_id, Song.user_id == user.id, Song.deleted.is_(False))
    )


@songs_bp.get("/<song_id>")
@login_required
def get_song(user, song_id: str):
    song = _owned_song(user, song_id)
    if song is None:
        return jsonify({"message": "Canción no encontrada"}), 404
    return jsonify(song.to_dict()), 200


@songs_bp.put("/<song_id>")
@songs_bp.patch("/<song_id>")
@login_required
def update_song(user, song_id: str):
    song = _owned_song(user, song_id)
    if song is None:
        return jsonify({"message": "Canción no encontrada"}), 404

    data = load(SongSchema(), request.get_json(silent=True) or {}, partial=True)
    if "tagIds" in data or "tagNames" in data:
        song.tags = _resolve_tags(user, data.pop("tagIds", []), data.pop("tagNames", []))
    data.pop("tagIds", None)
    data.pop("tagNames", None)

    field_map = {
        "title": "title",
        "artist": "artist",
        "key": "key",
        "capo": "capo",
        "bpm": "bpm",
        "timeSignature": "time_signature",
        "content": "content",
        "contentJson": "content_json",
        "hasChords": "has_chords",
        "notes": "notes",
    }
    for key, attr in field_map.items():
        if key in data:
            setattr(song, attr, data[key])
    song.touch()
    db.session.commit()
    return jsonify(song.to_dict()), 200


@songs_bp.delete("/<song_id>")
@login_required
def delete_song(user, song_id: str):
    song = _owned_song(user, song_id)
    if song is None:
        return jsonify({"message": "Canción no encontrada"}), 404
    song.deleted = True
    song.touch()
    db.session.commit()
    return "", 204


@songs_bp.get("/meta/filters")
@login_required
def filter_meta(user):
    """Valores disponibles para poblar la UI de filtros."""
    artists = db.session.scalars(
        select(Song.artist)
        .where(Song.user_id == user.id, Song.deleted.is_(False), Song.artist != "")
        .distinct()
        .order_by(Song.artist)
    ).all()
    keys = db.session.scalars(
        select(Song.key)
        .where(Song.user_id == user.id, Song.deleted.is_(False))
        .distinct()
    ).all()
    tags = db.session.scalars(
        select(Tag).where(Tag.user_id == user.id, Tag.deleted.is_(False)).order_by(Tag.name)
    ).all()
    return jsonify(
        {
            "artists": list(artists),
            "keys": list(keys),
            "tags": [{"id": t.id, "name": t.name, "color": t.color} for t in tags],
        }
    ), 200
