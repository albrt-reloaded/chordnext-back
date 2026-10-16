"""Etiquetas reutilizables por usuario."""

from ..extensions import db
from .base import SyncMixin, TimestampMixin, UUIDMixin

song_tags = db.Table(
    "song_tags",
    db.Column("song_id", db.String(36), db.ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.String(36), db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(UUIDMixin, TimestampMixin, SyncMixin, db.Model):
    __tablename__ = "tags"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(16), default="#6366f1")

    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_tag_user_name"),)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "color": self.color,
            "revision": self.revision,
            "deleted": self.deleted,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tag {self.name}>"
