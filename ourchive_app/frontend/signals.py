from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import caches, cache
from django.utils.cache import get_cache_key
from django.urls import reverse
from django.http import HttpRequest
from django.db import connections
from django.core.cache.backends.db import DatabaseCache
from api import models as api

def make_key(key, key_prefix, version):
    return f"ourchive:{version}:{key}"

@receiver(post_save, sender=api.Work)
def spoil_cache_create(sender, instance, created, **kwargs):
    if created:
        print('created')

@receiver(post_save, sender=api.Work)
def spoil_work_cache_update(sender, instance, **kwargs):
    connection = connections['default']
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM ourchive_database_cache where cache_key like 'ourchive:%:work_{instance.id}_%'")

@receiver(post_save, sender=api.Chapter)
def spoil_chapter_cache_update(sender, instance, **kwargs):
    connection = connections['default']
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM ourchive_database_cache where cache_key like 'ourchive:%:work_{instance.work_id}_%'")