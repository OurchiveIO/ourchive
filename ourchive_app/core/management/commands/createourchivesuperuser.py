import logging
import os
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create a superuser for the website."

    def generate_data(self):
        from django.contrib.auth import get_user_model
        username = os.getenv('OURCHIVE_SUPERUSER_NAME')
        if get_user_model().objects.filter(username=username).exists():
            return
        password = os.getenv('OURCHIVE_SUPERUSER_PASSWORD')
        email = os.getenv('OURCHIVE_SUPERUSER_EMAIL')
        get_user_model().objects.create_superuser(username, email, password)
        user = get_user_model().objects.filter(username=username).first()
        user.can_upload_audio = True
        user.can_upload_video = True
        user.can_upload_document = True
        user.can_upload_images = True
        user.can_upload_export_files = True
        user.save()



    def handle(self, *args, **options):
        self.generate_data()
        print('Superuser created.')
