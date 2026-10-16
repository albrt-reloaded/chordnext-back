"""Mixins reutilizables para los modelos."""

import uuid
from datetime import datetime, timezone

from ..extensions import db


def _uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDMixin:
    id = db.Column(db.String(36), primary_key=True, default=_uuid)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class SyncMixin:
    """Campos que habilitan la sincronización offline-first.

    `revision` se incrementa en cada cambio para detección de conflictos;
    `deleted` implementa soft-delete para propagar borrados en el pull.
    """

    revision = db.Column(db.Integer, default=1, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)

    def touch(self):
        self.revision = (self.revision or 0) + 1
        self.updated_at = utcnow()
