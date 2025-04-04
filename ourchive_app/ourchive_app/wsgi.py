"""
WSGI config for ourchive_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ourchive_app.settings.base')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
