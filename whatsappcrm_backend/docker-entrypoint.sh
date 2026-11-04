#!/bin/sh
# Backend web container start-up: bring the database schema up to date, then serve.
#
# Without this, pulling new code and restarting the container serves it against
# the old schema until someone remembers to run `migrate` by hand — which is how
# /crm-api/tours/ came to return 500 (and online booking stopped) in Nov 2026.
#
# Only the web container runs this. The Celery workers and beat start from the
# same code but never migrate, so two processes never race on one migration.
set -e

attempt=1
until python manage.py migrate --noinput; do
  # The database container may still be starting; give it up to ~1 minute.
  if [ "$attempt" -ge 12 ]; then
    echo "migrate failed after $attempt attempts; not starting the web server." >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 5
done

exec daphne -b 0.0.0.0 -p 8000 whatsappcrm_backend.asgi:application
