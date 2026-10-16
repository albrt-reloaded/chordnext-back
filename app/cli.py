"""Comandos CLI personalizados (`flask ...`)."""

import click
from flask import Flask
from flask.cli import with_appcontext

from .extensions import db
from .models import Progression, Song, Tag, User


def register_cli(app: Flask) -> None:
    app.cli.add_command(create_tables)
    app.cli.add_command(seed_demo)


@click.command("create-tables")
@with_appcontext
def create_tables():
    """Crea todas las tablas directamente (sin Alembic)."""
    db.create_all()
    click.echo("Tablas creadas.")


@click.command("seed-demo")
@with_appcontext
def seed_demo():
    """Crea un usuario demo con canciones, etiquetas y progresiones."""
    email = "demo@chordnext.app"
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, name="Demo", provider="local")
        user.set_password("demo1234")
        db.session.add(user)
        db.session.flush()

    worship = Tag(user_id=user.id, name="Adoración", color="#f59e0b")
    rock = Tag(user_id=user.id, name="Rock", color="#ef4444")
    db.session.add_all([worship, rock])
    db.session.flush()

    songs = [
        Song(
            user_id=user.id,
            title="Sublime Gracia",
            artist="Tradicional",
            key="G",
            bpm=72,
            content="[G]Sublime [C]gracia, [G]dulce el [D]son\n[G]que salvó [C]a un [G]tal como [D]yo",
            has_chords=True,
            tags=[worship],
        ),
        Song(
            user_id=user.id,
            title="Como Corza",
            artist="Anónimo",
            key="D",
            bpm=88,
            content="[D]Como la [A]corza busca el [Bm]agua\n[G]así te busca [A]mi [D]alma",
            has_chords=True,
            tags=[worship],
        ),
        Song(
            user_id=user.id,
            title="Noche de Rock",
            artist="Los Acordes",
            key="A",
            bpm=132,
            content="[A]Enciende el [D]ampli [E]otra vez",
            has_chords=True,
            tags=[rock],
        ),
    ]
    db.session.add_all(songs)

    db.session.add_all(
        [
            Progression(user_id=user.id, name="Pop clásico", degrees="I-V-vi-IV", key="C", preferred=True),
            Progression(user_id=user.id, name="Cadencia Andaluza", degrees="i-VII-VI-V", key="Am", preferred=True),
            Progression(user_id=user.id, name="Blues 12", degrees="I-I-I-I-IV-IV-I-I-V-IV-I-V", key="A"),
        ]
    )
    db.session.commit()
    click.echo(f"Usuario demo creado: {email} / demo1234")
