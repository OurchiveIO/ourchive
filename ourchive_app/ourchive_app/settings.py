"""
Django settings for ourchive_app project.

"""

import os
from dotenv import load_dotenv, find_dotenv
from django.utils.translation import gettext_lazy as _


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(find_dotenv())

APPEND_SLASH = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('OURCHIVE_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('OURCHIVE_DEBUG') == 'True'

hosts = []
if os.getenv('OURCHIVE_DEV') == 'True' or DEBUG:
    hosts = ["127.0.0.1:8000", "*",]
else:
    hosts = [os.getenv("OURCHIVE_ROOT_URL"), os.getenv("OURCHIVE_SERVER_IP")]

ALLOWED_HOSTS = hosts

API_PROTOCOL = 'http://' if DEBUG else 'https://'
ROOT_URL = os.getenv('OURCHIVE_ROOT_URL')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'frontend',
    'django.contrib.postgres',
    'corsheaders',
    'anymail',
    'api',
    'etl',
    'django_apscheduler'
    #'background_task',
]

if not DEBUG:
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        #'django.middleware.cache.UpdateCacheMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        #'django.middleware.cache.FetchFromCacheMiddleware',
    ]
else:
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

TMP_ROOT = os.getenv('OURCHIVE_TMP_ROOT')

FILE_PROCESSOR = 'local'

S3_BUCKET = 'ourchive_media'

SEARCH_BACKEND = 'POSTGRES'

TAG_DIVIDER = '$!$'

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR+"/sent_emails"
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
        "DIRS": [os.path.join(BASE_DIR,"templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'frontend.context_processors.set_style',
                'frontend.context_processors.set_has_notifications',
                'frontend.context_processors.set_content_pages',
                'frontend.context_processors.set_captcha',
                'frontend.context_processors.load_settings',
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
        'NAME': 'ourchive_db',
        'USER': 'ourchive',
        'PASSWORD': os.getenv('OURCHIVE_DB_PW'),
        'HOST': os.getenv('OURCHIVE_DB_HOST'),
        'PORT': '5432',
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

AUTH_USER_MODEL = 'api.User'


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

#CACHE_MIDDLEWARE_ALIAS = "default"
#CACHE_MIDDLEWARE_SECONDS = 3600
#CACHE_MIDDLEWARE_KEY_PREFIX = ""


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.custom_exception_handler.custom_exception_handler',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.custom_pagination.CustomPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/day',
        'user': '10000/day'
    }
}

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
            'class': 'logging.FileHandler',
            'filename': 'ourchive.log',
            'formatter': 'simple',
        }
    },
    'loggers': {
        '': {
            'level':  os.getenv("OURCHIVE_LOG_LEVEL", "INFO"),
            'handlers': ['file'],
        },
    },
}

if not DEBUG:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": os.getenv('OURCHIVE_DJANGO_CACHE'),
        }
    }
