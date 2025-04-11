"""
Django settings for ourchive_app project.

"""

import os
from dotenv import load_dotenv, find_dotenv
from django.utils.translation import gettext_lazy as _


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

if not os.getenv('OURCHIVE_DOCKER', False):
    load_dotenv(find_dotenv())

APPEND_SLASH = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('OURCHIVE_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('OURCHIVE_DEBUG', False) == 'True'

hosts = ["0.0.0.0", "localhost", "127.0.0.1"]
if os.getenv('OURCHIVE_DEV') == 'True' or DEBUG:
    hosts = hosts + ["127.0.0.1:8000", "*", ]
else:
    hosts = hosts + [os.getenv("OURCHIVE_ROOT_URL"), os.getenv("OURCHIVE_SERVER_IP")]

ALLOWED_HOSTS = hosts

API_PROTOCOL = f"{os.getenv('OURCHIVE_SCHEME', 'http')}://"
ROOT_URL = os.getenv('OURCHIVE_ROOT_URL')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oauth2_provider',
    'rest_framework',
    'core',
    'frontend',
    'django.contrib.postgres',
    'corsheaders',
    'anymail',
    'search',
    'api',
    'etl',
    'django_apscheduler'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1:8000',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    'http://127.0.0.1:8000',
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
]

CAPTCHA_SITE_KEY = os.environ.get('OURCHIVE_CAPTCHA_SITE_KEY')
CAPTCHA_SECRET = os.environ.get('OURCHIVE_CAPTCHA_SECRET')
USE_CAPTCHA = os.environ.get('OURCHIVE_USE_CAPTCHA')
CAPTCHA_PROVIDER = os.environ.get('OURCHIVE_CAPTCHA_PROVIDER')
CAPTCHA_PARAM = os.environ.get('OURCHIVE_CAPTCHA_PARAM')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = 'ourchive_app.urls'

MEDIA_ROOT = os.getenv('OURCHIVE_MEDIA_ROOT')

MEDIA_URL = os.getenv('OURCHIVE_MEDIA_URL')

TMP_ROOT = os.getenv('OURCHIVE_TMP_ROOT', 'tmp')

SCRIPTS_ROOT = os.getenv('OURCHIVE_SCRIPTS_ROOT', 'scripts')

FILE_PROCESSOR = os.getenv('OURCHIVE_FILE_PROCESSOR')

S3_BUCKET = os.getenv('OURCHIVE_S3_BUCKET')

SEARCH_BACKEND = 'POSTGRES'

TAG_DIVIDER = '$!$'

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR + "/sent_emails"
else:
    ANYMAIL = {
        "MAILGUN_API_KEY": os.getenv("OURCHIVE_MAILGUN_API_KEY"),
        "MAILGUN_SENDER_DOMAIN": os.getenv("OURCHIVE_MAILGUN_SENDER_DOMAIN"),
    }
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("OURCHIVE_DEFAULT_FROM_EMAIL")
SERVER_EMAIL = os.getenv("OURCHIVE_SERVER_EMAIL")


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'frontend.context_processors.set_user_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'ourchive_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('OURCHIVE_DB_NAME', 'ourchive_db'),
        'USER': os.getenv('OURCHIVE_DB_USER', 'ourchive'),
        'PASSWORD': os.getenv('OURCHIVE_DB_PW'),
        'HOST': os.getenv('OURCHIVE_DB_HOST'),
        'PORT': os.getenv('OURCHIVE_DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = 'core.User'


LOCALE_PATHS = [
    f'{BASE_DIR}/locale/',
]

LANGUAGES = [
    ('en', _('English')),
]
LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = f"{ os.getenv('OURCHIVE_SCHEME', 'http') }://{ os.getenv('OURCHIVE_DOMAIN', 'localhost:9000') }/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

OAUTH2_PROVIDER = {
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
}

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.custom_exception_handler.custom_exception_handler',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.custom_pagination.CustomPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '200000/day',
        'user': '500000/day'
    },
}

LOGIN_URL = '/admin/login/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{name} {levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level' : 'INFO' if not DEBUG else 'DEBUG',
            'maxBytes' : 1024*1024*10, # 10MB
            'backupCount' : 10,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'ourchive.log',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        '': {
            'level': os.getenv("OURCHIVE_LOG_LEVEL", "INFO"),
            'handlers': ['file'],
        },
    },
}

# data autogen properties
CHAPTER_AUDIO_URLS = [
]

CHAPTER_VIDEO_URLS = [
]

CHAPTER_IMAGE_URLS = [
]

CHIVE_HEADER_URLS = [
]

CHIVE_COVER_URLS = [
]

if not DEBUG and os.getenv('OURCHIVE_CACHE', False):
    CACHE_MIDDLEWARE_ALIAS = "default"
    CACHE_MIDDLEWARE_SECONDS = 3600
    CACHE_MIDDLEWARE_KEY_PREFIX = ""
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": 'ourchive_database_cache',
            "KEY_FUNCTION": "frontend.signals.make_key"
        }
    }
else:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }}
