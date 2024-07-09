from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.core.cache import caches, cache
from django.utils.cache import get_cache_key
from django.urls import reverse
from django.http import HttpRequest
from django.db import connections
from django.core.cache.backends.db import DatabaseCache
from core import models as core

def make_key(key, key_prefix, version):
    return f"ourchive:{version}:{key}"

def spoil_work_cache(instance):
    connection = connections['default']
    all_tables = connection.introspection.table_names()
    if 'ourchive_database_cache' not in all_tables:
        return
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM ourchive_database_cache where cache_key like 'ourchive:%:work_{instance.id}_%'")

def spoil_subscription_cache(instance):
    connection = connections['default']
    all_tables = connection.introspection.table_names()
    if 'ourchive_database_cache' not in all_tables:
        return
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM ourchive_database_cache where cache_key like %s", [f'ourchive:%:subscription_{instance.user.username}_%'])

def spoil_bookmark_cache(instance):
    connection = connections['default']
    all_tables = connection.introspection.table_names()
    if 'ourchive_database_cache' not in all_tables:
        return
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM ourchive_database_cache where cache_key like 'ourchive:%:bookmark_{instance.id}_%'")
        cursor.execute(f"DELETE FROM ourchive_database_cache where cache_key like 'ourchive:%:collection_{instance.id}_%'")

def spoil_collection_cache(instance):
    connection = connections['default']
    all_tables = connection.introspection.table_names()
    if 'ourchive_database_cache' not in all_tables:
        return
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM ourchive_database_cache where cache_key like 'ourchive:%:collection_{instance.id}_%'")

@receiver(post_save, sender=core.Work)
def spoil_cache_create(sender, instance, created, **kwargs):
    if created:
        return True

@receiver(post_save, sender=core.Work)
def spoil_work_cache_update(sender, instance, **kwargs):
    spoil_work_cache(instance)

@receiver(post_save, sender=core.UserWork)
def spoil_work_user_cache_update(sender, instance, **kwargs):
    spoil_work_cache(instance.work)

@receiver(post_save, sender=core.UserWork)
def spoil_work_user_cache_delete(sender, instance, **kwargs):
    spoil_work_cache(instance.work)

@receiver(post_delete, sender=core.Work)
def spoil_work_cache_delete(sender, instance, **kwargs):
    spoil_work_cache(instance)

@receiver(post_save, sender=core.Chapter)
def spoil_chapter_cache_update(sender, instance, **kwargs):
    spoil_work_cache(instance.work)

@receiver(pre_delete, sender=core.Chapter)
def spoil_chapter_cache_delete(sender, instance, **kwargs):
    spoil_work_cache(instance.work)

@receiver(post_save, sender=core.UserSubscription)
def spoil_subscription_cache_update(sender, instance, **kwargs):
    spoil_subscription_cache(instance)

@receiver(post_delete, sender=core.UserSubscription)
def spoil_subscription_cache_delete(sender, instance, **kwargs):
    spoil_subscription_cache(instance)

@receiver(post_save, sender=core.Bookmark)
def spoil_bookmark_cache_update(sender, instance, **kwargs):
    spoil_bookmark_cache(instance)

@receiver(post_delete, sender=core.Bookmark)
def spoil_bookmark_cache_delete(sender, instance, **kwargs):
    spoil_bookmark_cache(instance)

@receiver(post_save, sender=core.BookmarkCollection)
def spoil_collection_cache_update(sender, instance, **kwargs):
    spoil_collection_cache(instance)

@receiver(post_delete, sender=core.BookmarkCollection)
def spoil_collection_cache_delete(sender, instance, **kwargs):
    spoil_collection_cache(instance)

@receiver(post_save, sender=core.UserCollection)
def spoil_user_collection_cache_update(sender, instance, **kwargs):
    spoil_collection_cache(instance.collection)

@receiver(pre_delete, sender=core.UserCollection)
def spoil_user_collection_cache_delete(sender, instance, **kwargs):
    spoil_collection_cache(instance.collection)