#!/bin/sh
# Entrypoint script for Docker: ensures DB is ready, runs migrations, collects static, and starts Gunicorn
# See README.md and inline comments for documentation.

set -e

# Wait for Postgres to be ready
until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT..."
  sleep 2
done

echo "Postgres is up - continuing."

# Run migrations
pipenv run python manage.py migrate --noinput

# Collect static files
pipenv run python manage.py collectstatic --noinput

# Start Gunicorn
exec pipenv run gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 