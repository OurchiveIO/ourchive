from ourchive_app.settings.base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('OURCHIVE_TEST_DB_NAME', 'ourchive_manual_test'),
        'USER': os.getenv('OURCHIVE_DB_USER', 'ourchive'),
        'PASSWORD': os.getenv('OURCHIVE_DB_PW'),
        'HOST': os.getenv('OURCHIVE_DB_HOST'),
        'PORT': os.getenv('OURCHIVE_DB_PORT', '5432'),
    }
}