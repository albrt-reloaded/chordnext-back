"""Progresiones armónicas reutilizables (ej. I - V - vi - IV)."""

from ..extensions import db
from .base import SyncMixin, TimestampMixin, UUIDMixin


class Progression(UUIDMixin, TimestampMixin, SyncMixin, db.Model):
    __tablename__ = "progressions"

    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    degrees = db.Column(db.String(255), nullable=False)   # "I-V-vi-IV"
    key = db.Column(db.String(8), default="C")
    preferred = db.Column(db.Boolean, default=False)      # mostrar en atajos rápidos

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "degrees": self.degrees,
            "key": self.key,
            "preferred": self.preferred,
            "revision": self.revision,
            "deleted": self.deleted,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Progression {self.name!r} ({self.degrees})>"
