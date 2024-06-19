#!/bin/bash

# This loads all the fixtures into the current environment.
python manage.py loaddata api/fixtures/ourchivesettings.yaml
python manage.py loaddata api/fixtures/attributetype.yaml
python manage.py loaddata api/fixtures/attributevalue.yaml
python manage.py loaddata api/fixtures/notificationtype.yaml
python manage.py loaddata api/fixtures/tagtype.yaml
python manage.py loaddata api/fixtures/worktype.yaml
python manage.py loaddata etl/fixtures/objectmapping.yaml
