"""CRUD de progresiones armónicas reutilizables."""

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from ..extensions import db
from ..models import Progression
from ..schemas import ProgressionSchema
from ._common import load, login_required

progressions_bp = Blueprint("progressions", __name__)


def _owned(user, prog_id: str) -> Progression | None:
    return db.session.scalar(
        select(Progression).where(
            Progression.id == prog_id, Progression.user_id == user.id, Progression.deleted.is_(False)
        )
    )


@progressions_bp.get("")
@login_required
def list_progressions(user):
    rows = db.session.scalars(
        select(Progression)
        .where(Progression.user_id == user.id, Progression.deleted.is_(False))
        .order_by(Progression.preferred.desc(), Progression.name)
    ).all()
    return jsonify({"items": [p.to_dict() for p in rows]}), 200


@progressions_bp.post("")
@login_required
def create_progression(user):
    data = load(ProgressionSchema(), request.get_json(silent=True) or {})
    prog = Progression(
        user_id=user.id,
        name=data["name"],
        degrees=data["degrees"],
        key=data["key"],
        preferred=data["preferred"],
    )
    db.session.add(prog)
    db.session.commit()
    return jsonify(prog.to_dict()), 201


@progressions_bp.put("/<prog_id>")
@progressions_bp.patch("/<prog_id>")
@login_required
def update_progression(user, prog_id: str):
    prog = _owned(user, prog_id)
    if prog is None:
        return jsonify({"message": "Progresión no encontrada"}), 404
    data = load(ProgressionSchema(), request.get_json(silent=True) or {}, partial=True)
    for key in ("name", "degrees", "key", "preferred"):
        if key in data:
            setattr(prog, key, data[key])
    prog.touch()
    db.session.commit()
    return jsonify(prog.to_dict()), 200


@progressions_bp.delete("/<prog_id>")
@login_required
def delete_progression(user, prog_id: str):
    prog = _owned(user, prog_id)
    if prog is None:
        return jsonify({"message": "Progresión no encontrada"}), 404
    prog.deleted = True
    prog.touch()
    db.session.commit()
    return "", 204
