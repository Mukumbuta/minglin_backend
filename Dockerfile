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
        netcat-openbsd \
        curl \
        git && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Create logs directory for Django logging (fallback)
RUN mkdir -p logs

# Collect static files (for production)
RUN python manage.py collectstatic --noinput

# Create non-root user for security
RUN useradd -m minglin && chown -R minglin /app

# Copy and set permissions for entrypoint script
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER minglin

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Health check to ensure container is running properly
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/healthcheck/ || exit 1

# Entrypoint script waits for DB, then runs migrations and starts Gunicorn
ENTRYPOINT ["/entrypoint.sh"]

# See README.md and Dockerfile comments for documentation. 