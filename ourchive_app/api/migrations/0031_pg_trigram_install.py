from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_bookmarkcollection_comment_count_collectioncomment'),
    ]

    operations = [
        TrigramExtension(),
    ]
