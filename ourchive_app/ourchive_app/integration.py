from ourchive_app.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('OURCHIVE_INTEGRATION_DB_NAME', 'ourchive_db_integration'),
        'USER': os.getenv('OURCHIVE_DB_USER', 'ourchive'),
        'PASSWORD': os.getenv('OURCHIVE_DB_PW'),
        'HOST': os.getenv('OURCHIVE_DB_HOST'),
        'PORT': os.getenv('OURCHIVE_DB_PORT', '5432'),
    }
}