#!/bin/sh
set -e

# run alembic migrations
alembic upgrade head

# start the app using uvicorn
exec uvicorn run:app --host 0.0.0.0 --port 8000
