import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Executes a SQL script with the provided filename."

    def add_arguments(self, parser):
        parser.add_argument("scripts", nargs="+", type=str)

    def execute_script(self, script):
        with connection.cursor() as cursor:
            script_file = open(f'{settings.SCRIPTS_ROOT}/{script}.sql')
            command = script_file.read()
            response = cursor.execute(command)
            script_file.close()
            return response

    def handle(self, *args, **options):
        for script in options['scripts']:
            self.execute_script(script)
        print('Scripts executed.')