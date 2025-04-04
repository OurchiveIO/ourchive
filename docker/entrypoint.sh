#!/usr/bin/env bash

set -euo pipefail

# Execute pending migrations
echo Executing pending migrations
python ourchive_app/manage.py migrate

# Load default data
echo Load default data
python ourchive_app/manage.py loadourchivedata

# Give permission to ourchive:ourchive after mounting volumes
echo Give permission to ourchive:ourchive
chown -R ourchive:ourchive /ourchive_app

# Start Ourchive processes
echo Starting Ourchive...
exec gosu ourchive gunicorn ourchive.wsgi:application \
    --name ourchive \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --worker-tmp-dir /dev/shm \
    --log-level=info \
    --access-logfile - \
    "$@"