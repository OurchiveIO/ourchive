from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import caches, cache
from django.utils.cache import get_cache_key
from django.urls import reverse
from django.http import HttpRequest
from django.db import connections
from django.core.cache.backends.db import DatabaseCache

from api.models import Work

def make_key(key, key_prefix, version):
    return f"ourchive:{version}:{key}"

@receiver(post_save, sender=Work)
def spoil_cache_create(sender, instance, created, **kwargs):
    if created:
        print('created')

@receiver(post_save, sender=Work)
def spoil_cache_update(sender, instance, **kwargs):
    connection = connections['default']
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM ourchive_database_cache where cache_key like f'ourchive:%:work_{instance.id}_%'")