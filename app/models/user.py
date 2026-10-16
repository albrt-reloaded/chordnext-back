"""Usuario y credenciales."""

from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from .base import SyncMixin, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, SyncMixin, db.Model):
    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, default="")
    avatar_url = db.Column(db.String(512))

    # Autenticación tradicional
    password_hash = db.Column(db.String(255))

    # OAuth Google
    provider = db.Column(db.String(32), nullable=False, default="local")
    google_id = db.Column(db.String(64), unique=True, index=True)

    # Preferencias (sincronizadas)
    preferred_key = db.Column(db.String(8), default="C")
    theme = db.Column(db.String(16), default="system")
    font_size = db.Column(db.Integer, default=16)

    songs = db.relationship("Song", back_populates="owner", lazy="dynamic")
    setlists = db.relationship("Setlist", back_populates="owner", lazy="dynamic")

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return bool(self.password_hash) and check_password_hash(self.password_hash, raw)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"
