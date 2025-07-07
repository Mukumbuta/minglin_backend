# Dockerfile for Django + Gunicorn + PostGIS
# -------------------------------------------
# This Dockerfile builds a production-ready Django container
# with Gunicorn as the WSGI server and PostGIS client libraries.

FROM python:3.12-slim as base

# Install system dependencies for PostGIS and psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        binutils \
        gdal-bin \
        postgis \
        netcat \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install pipenv
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile

# Copy project files
COPY . .

# Collect static files (for production)
RUN pipenv run python manage.py collectstatic --noinput

# Create non-root user for security
RUN useradd -m myuser && chown -R myuser /app
USER myuser

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Health check to ensure container is running properly
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/healthcheck/ || exit 1

# Entrypoint script waits for DB, then runs migrations and starts Gunicorn
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# See README.md and Dockerfile comments for documentation. 