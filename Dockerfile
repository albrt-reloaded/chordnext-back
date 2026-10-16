FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 5000

# Aplica las migraciones y arranca gunicorn.
CMD ["sh", "-c", "flask --app wsgi:app db upgrade && gunicorn -b 0.0.0.0:${PORT} --workers 3 --timeout 60 wsgi:app"]
