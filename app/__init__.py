"""App factory de ChordNext."""

from flask import Flask, jsonify

from .config import Config
from .extensions import cors, db, jwt, ma, migrate


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    _register_extensions(app)
    _register_blueprints(app)
    _register_jwt_handlers(app)
    _register_error_handlers(app)
    _register_cli(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "chordnext-api"}

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # Importa los modelos para que Alembic los detecte.
    from . import models  # noqa: F401


def _register_blueprints(app: Flask) -> None:
    from .api.auth import auth_bp
    from .api.songs import songs_bp
    from .api.setlists import setlists_bp
    from .api.tags import tags_bp
    from .api.progressions import progressions_bp
    from .api.sync import sync_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(songs_bp, url_prefix="/api/songs")
    app.register_blueprint(setlists_bp, url_prefix="/api/setlists")
    app.register_blueprint(tags_bp, url_prefix="/api/tags")
    app.register_blueprint(progressions_bp, url_prefix="/api/progressions")
    app.register_blueprint(sync_bp, url_prefix="/api/sync")


def _register_cli(app: Flask) -> None:
    from .cli import register_cli

    register_cli(app)


def _register_jwt_handlers(app: Flask) -> None:
    @jwt.unauthorized_loader
    def _missing(reason):
        return jsonify({"message": "Autenticación requerida", "detail": reason}), 401

    @jwt.invalid_token_loader
    def _invalid(reason):
        return jsonify({"message": "Token inválido", "detail": reason}), 422

    @jwt.expired_token_loader
    def _expired(header, payload):
        return jsonify({"message": "Token expirado", "code": "token_expired"}), 401


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def _not_found(_):
        return jsonify({"message": "Recurso no encontrado"}), 404

    @app.errorhandler(422)
    def _unprocessable(err):
        return jsonify({"message": "Datos inválidos", "errors": getattr(err, "data", None)}), 422

    @app.errorhandler(500)
    def _server_error(_):
        return jsonify({"message": "Error interno del servidor"}), 500
