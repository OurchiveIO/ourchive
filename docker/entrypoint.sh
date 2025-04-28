#!/usr/bin/env bash

set -euo pipefail

# Execute pending migrations
echo Executing pending migrations
python manage.py migrate

# Load default data
echo Load default data
python manage.py loadourchivedata

# Create superuser
echo Create superuser
python manage.py createourchivesuperuser

# Give permission to ourchive:ourchive after mounting volumes
echo Give permission to ourchive:ourchive
chown -R ourchive:ourchive /ourchive_app

# Start scheduler
echo Running apscheduler...
nohup python manage.py runapscheduler &

# Start Ourchive processes
echo Starting Ourchive...
exec gosu ourchive gunicorn ourchive_app.wsgi:application \
    --name ourchive \
    --bind 0.0.0.0:8000 \
    --timeout=5 \
    --worker-class=gevent \
    --workers 3 \
    --worker-tmp-dir /dev/shm \
    --log-level=info \
    --access-logfile - \
    --error-logfile - \
    "$@"