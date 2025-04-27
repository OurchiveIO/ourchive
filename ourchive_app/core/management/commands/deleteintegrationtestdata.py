import logging
from django.core.management.base import BaseCommand
from core.models import Work, Anthology, WorkSeries, BookmarkCollection, Bookmark, UserSubscription
from datetime import datetime, time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Removes data created by integration tests."

    def remove_data(self, **options):
        delete_date = datetime.combine(datetime.now().date(), time())
        if options.get('works') == 'y':
            Work.objects.filter(updated_on__gte=delete_date).delete()
        if options.get('anthologies') == 'y':
            Anthology.objects.filter(updated_on__gte=delete_date).delete()
        if options.get('series') == 'y':
            WorkSeries.objects.filter(updated_on__gte=delete_date).delete()
        if options.get('collections') == 'y':
            BookmarkCollection.objects.filter(updated_on__gte=delete_date).delete()
        if options.get('bookmarks') == 'y':
            Bookmark.objects.filter(updated_on__gte=delete_date).delete()
        if options.get('subscriptions') == 'y':
            UserSubscription.objects.filter(updated_on__gte=delete_date).delete()

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "-w", "--works",
            help="Delete works y/n? Default: y",
            default='y',
        )
        parser.add_argument(
            "-a", "--anthologies",
            help="Delete anthologies y/n? Default: y",
            default='y',
        )
        parser.add_argument(
            "-s", "--series",
            help="Delete series y/n? Default: y",
            default='y',
        )
        parser.add_argument(
            "-c", "--collections",
            help="Delete collections y/n? Default: y",
            default='y',
        )
        parser.add_argument(
            "-b", "--bookmarks",
            help="Delete bookmarks y/n? Default: y",
            default='y',
        )
        parser.add_argument(
            "-sb", "--subscriptions",
            help="Delete subscriptions y/n? Default: y",
            default='y',
        )

    def handle(self, *args, **options):
        self.remove_data(**options)
        print('Data deleted.')
