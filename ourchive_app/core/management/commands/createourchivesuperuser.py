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
        try:
            get_user_model().objects.create_superuser(username.lower(), email, password)
        except:
            print(f'Superuser creation failed. Superuser might be a duplicate, or OURCHIVE_SUPERUSER_NAME or other env variable is missing. Username: {username} Email: {email}')
            return False
        user = get_user_model().objects.filter(username=username.lower()).first()
        if not user:
            print(f'Superuser cannot be found. Username: {username}')
            return False
        user.can_upload_audio = True
        user.can_upload_video = True
        user.can_upload_document = True
        user.can_upload_images = True
        user.can_upload_export_files = True
        user.save()
        return True


    def handle(self, *args, **options):
        try:
            ret = self.generate_data()
            if ret:
                print('Superuser created.')
        except:
            print('Error occurred creating superuser. Create a superuser manually using the management console.')
