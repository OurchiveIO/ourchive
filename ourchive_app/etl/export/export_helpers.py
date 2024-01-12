from django.conf import settings
from zipfile import ZipFile
import os
import io
import shutil

def clean_text(text):
    return "".join([c for c in text if c.isalpha() or c.isdigit() or c==' ']).rstrip()


def get_temp_directory(username, uuid):
    return f'{settings.TMP_ROOT}/chive_export/{uuid}/{clean_text(username)}/'


def get_media_directory(username, uuid):
    return f'{settings.MEDIA_ROOT}/chive_export/{uuid}/{clean_text(username)}/'


def get_media_url(username, uuid):
    return f'{settings.MEDIA_URL}chive_export/{uuid}/{clean_text(username)}/'


def get_zip_dir(username, uuid):
    clean_username = clean_text(username)
    return f"{get_media_directory(username, uuid)}{clean_username}.zip"


def get_zip_url(username, uuid):
    clean_username = clean_text(username)
    return f"{get_media_url(username, uuid)}{clean_username}.zip"