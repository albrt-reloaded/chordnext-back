"""Canción: estructura, letra y acordes."""

from ..extensions import db
from .base import SyncMixin, TimestampMixin, UUIDMixin
from .tag import song_tags


class Song(UUIDMixin, TimestampMixin, SyncMixin, db.Model):
    __tablename__ = "songs"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = db.Column(db.String(255), nullable=False, index=True)
    artist = db.Column(db.String(255), default="", index=True)

    # Armonía
    key = db.Column(db.String(8), default="C", index=True)          # tono original
    capo = db.Column(db.Integer, default=0)
    bpm = db.Column(db.Integer, default=90, index=True)
    time_signature = db.Column(db.String(8), default="4/4")

    # Contenido
    # `content` guarda el texto ChordPro ([C]letra...).
    # `content_json` guarda la estructura rica: { sections: [{type, lines:[{chords:[{pos,chord}], text}]}] }
    content = db.Column(db.Text, default="")
    content_json = db.Column(db.JSON)

    has_chords = db.Column(db.Boolean, default=True, index=True)
    notes = db.Column(db.Text, default="")

    owner = db.relationship("User", back_populates="songs")
    tags = db.relationship("Tag", secondary=song_tags, lazy="joined")
    setlist_items = db.relationship("SetlistItem", back_populates="song", cascade="all, delete-orphan")

    def to_dict(self, with_relations: bool = True) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "artist": self.artist,
            "key": self.key,
            "capo": self.capo,
            "bpm": self.bpm,
            "timeSignature": self.time_signature,
            "content": self.content,
            "contentJson": self.content_json,
            "hasChords": self.has_chords,
            "notes": self.notes,
            "revision": self.revision,
            "deleted": self.deleted,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        if with_relations:
            data["tags"] = [{"id": t.id, "name": t.name, "color": t.color} for t in self.tags]
        return data

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Song {self.title!r} - {self.artist!r}>"
