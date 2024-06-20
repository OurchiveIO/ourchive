import logging
from django.core.management.base import BaseCommand
from ourchive_app.util.ourchive_fakes import OurchiveFakes

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create test data to populate an integration test database."

    def generate_data(self, obj_count, token, create_dependency_objs):
        faker = OurchiveFakes()
        faker.generate_everything(obj_count, token, create_dependency_objs)

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "-n", "--num_instances",
            help="The max number of instances to create for chives, news items, "
                 "announcements, or notifications. Default: 10.",
            default=10,
        )
        parser.add_argument(
            "-t", "--token",
            help="A string that will be appended to object titles (e.g. for search use cases).",
            default='',
        )
        parser.add_argument(
            "-s", "--skip_unique",
            help="If y, will skip data with uniqueness requirements, like users and attribute types. "
                 "Use if you've run this tool before but want more chives.",
            default='n',
        )

    def handle(self, *args, **options):
        try:
            obj_count = int(options.get('num_instances'))
        except ValueError:
            print(f'-n flag must be a number. You typed: {options.get("num_instances")}')
            return
        token = options.get('token')
        create_dependency_objs = options.get('skip_unique').lower() == 'n'
        self.generate_data(obj_count, token, create_dependency_objs)
        print('Data created.')
