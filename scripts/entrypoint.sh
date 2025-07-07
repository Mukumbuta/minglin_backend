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

# Fix permissions for mounted volumes (run as root)
echo "Fixing permissions for mounted volumes..."
chown -R minglin:minglin /app
chmod -R 755 /app/api/migrations

# Switch to minglin user for running Django commands
exec gosu minglin /bin/sh -c "
  # Create migrations if they don't exist
  python manage.py makemigrations --noinput

  # Run migrations
  python manage.py migrate --noinput

  # Collect static files
  python manage.py collectstatic --noinput

  # Start Gunicorn
  exec gunicorn minglin_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3
" 