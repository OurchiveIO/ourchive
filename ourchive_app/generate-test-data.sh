#!/bin/bash

# Run migrations, load required data with flag to skip non-required, load fake data.
python manage.py migrate --settings=ourchive_app.settings.integration
python manage.py loadourchivedata --settings=ourchive_app.settings.integration -l n
python manage.py createintegrationtestdata --settings=ourchive_app.settings.integration