#!/bin/sh
# Deployment entry point for Render / similar platforms
cd "$(dirname "$0")"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Seed sample data + ensure a superuser exists (idempotent)
python seed_data.py || true

# Start the app server
exec gunicorn cricportal.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
