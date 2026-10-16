"""Cancioneros (setlists) e items ordenados."""

from ..extensions import db
from .base import SyncMixin, TimestampMixin, UUIDMixin


class Setlist(UUIDMixin, TimestampMixin, SyncMixin, db.Model):
    __tablename__ = "setlists"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")

    owner = db.relationship("User", back_populates="setlists")
    items = db.relationship(
        "SetlistItem",
        back_populates="setlist",
        cascade="all, delete-orphan",
        order_by="SetlistItem.position",
    )

    def to_dict(self, with_items: bool = True) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "revision": self.revision,
            "deleted": self.deleted,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        if with_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Setlist {self.name!r}>"


class SetlistItem(UUIDMixin, db.Model):
    __tablename__ = "setlist_items"

    setlist_id = db.Column(db.String(36), db.ForeignKey("setlists.id", ondelete="CASCADE"), nullable=False, index=True)
    song_id = db.Column(db.String(36), db.ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True)

    position = db.Column(db.Integer, default=0, nullable=False)
    key_override = db.Column(db.String(8))          # transposición fijada para el setlist
    notes = db.Column(db.Text, default="")

    setlist = db.relationship("Setlist", back_populates="items")
    song = db.relationship("Song", back_populates="setlist_items")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "setlist_id": self.setlist_id,
            "song_id": self.song_id,
            "position": self.position,
            "keyOverride": self.key_override,
            "notes": self.notes,
            "song": self.song.to_dict(with_relations=False) if self.song else None,
        }
