from django.core.management.base import BaseCommand
from ourchive_app.util import ourchive_fixtures


class Command(BaseCommand):
    help = "Load required data for a new Ourchive instance."

    @staticmethod
    def load_fixture_data(path, required_filename, optional_filename, load_optional):
        print(f'Loading data. Path: {path}, required data file: {required_filename},'
              f'optional data file: {optional_filename}, load optional data: {load_optional}')
        try:
            ourchive_fixtures.load_data(path, required_filename)
        except Exception as e:
            print(f'Could not load required data. Please check path or refer to repo defaults. Error: {e}')
            return
        if not load_optional:
            return
        try:
            ourchive_fixtures.load_data(path, optional_filename)
        except Exception as e:
            print(f'Could not load recommended data. Please check path or refer to repo defaults. Error: {e}')
            return
        print('Data loaded successfully.')

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "-p", "--fixture_path",
            help="The path for the fixtures folder. Default: core/fixtures/",
            default="core/fixtures/",
        )
        parser.add_argument(
            "-f", "--required_fixture",
            help="The name of the required fixtures file. Default: required_data.yaml",
            default="required_data.yaml",
        )
        parser.add_argument(
            "-o", "--optional_fixture",
            help="The name of the optional fixtures file. Default: recommended_data.yaml",
            default="recommended_data.yaml",
        )
        parser.add_argument(
            "-l", "--load_optional",
            help="If n, does not load recommended data. Default: y.",
            default="y",
        )

    def handle(self, *args, **options):
        recommended_data = options.get('load_optional').lower()
        load_optional = recommended_data == 'y' or recommended_data == 'yes'
        self.load_fixture_data(options.get('fixture_path'), options.get('required_fixture'),
                               options.get('optional_fixture'), load_optional)
        print('Data loaded.')
