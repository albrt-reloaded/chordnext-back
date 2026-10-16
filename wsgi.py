"""Punto de entrada WSGI / CLI.

Uso:
    flask --app wsgi:app run --debug
    flask --app wsgi:app db upgrade
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
