from django.test import TestCase
import core.models as models
from ourchive_app.util.ourchive_fakes import OurchiveFakes


class CoreTests(TestCase):
    fixtures = ['ourchivesettings', 'notificationtype']

    @classmethod
    def setUpTestData(cls):
        cls.ourchive_fakes = OurchiveFakes()
        cls.ourchive_fakes.generate_users(20, True)

    def test_fake_users(self):
        users = models.User.objects.all()
        self.assertEquals(20, len(users))

    def test_fake_works(self):
        works = self.ourchive_fakes.generate_works(models.User.objects.all().first().id, 30, True, 5, **{'token': 'untitled'})[0]
        self.assertEquals(30, len(works))
        self.assertEquals(5, len(works[0].chapters.all()))

    def test_fake_bookmarks(self):
        bookmarks = self.ourchive_fakes.generate_bookmarks(models.User.objects.all().first().id, 30, True, **{'token': 'untitled'})
        self.assertEquals(30, len(bookmarks))

    def test_fake_tags(self):
        tags = self.ourchive_fakes.generate_tags(30, True, **{'token': 'untitled', 'create_tag_types': True})
        self.assertEquals(30, len(tags))

    def test_fake_attributes(self):
        attributes = self.ourchive_fakes.generate_attributes(32, True, **{'token': 'untitled', 'create_attribute_types': True, 'attribute_type_count': 11})
        self.assertEquals(32, len(attributes))
        self.assertEquals(models.AttributeType.objects.count(), 11)

    def test_fake_works_no_save(self):
        works_and_chapters = self.ourchive_fakes.generate_works(models.User.objects.all().first().id, 30, False, 5)
        self.assertEquals(30, len(works_and_chapters[0]))
        self.assertEquals(5, len(works_and_chapters[1]))

    def test_fake_work_types(self):
        type_names = ['Fic', 'Vid', 'Podfic', 'Art']
        types = self.ourchive_fakes.generate_work_types(4, True, **{'type_names': type_names})
        self.assertEquals(4, len(types))
        self.assertIsNotNone(models.WorkType.objects.filter(type_name=type_names[1]).first().id)

    def test_fake_collections(self):
        collections_opts = {
            'assign_works': False,
            'create_works': True,
            'works_count': 10,
            'create_tags': True,
            'tags_count': 20,
            'create_attributes': True,
            'attributes_count': 10,
            'create_languages': True
        }
        collections = self.ourchive_fakes.generate_collections(
            models.User.objects.all().first().id,
            20,
            True,
            **collections_opts
        )
        self.assertEquals(20, len(collections))
        self.assertEquals(10, len(collections[0].works.all()))

    def test_settings_choices(self):
        settings_choices = models.Settings.choices
        self.assertIsNotNone(settings_choices)

    def test_fake_anthologies(self):
        anthologies_opts = {
            'create_works': True,
            'works_count': 12,
            'create_tags': True,
            'tags_count': 15,
            'create_attributes': True,
            'attributes_count': 13,
            'create_languages': True
        }
        anthologies = self.ourchive_fakes.generate_anthologies(
            models.User.objects.all().first().id,
            13,
            True,
            **anthologies_opts
        )
        self.assertEquals(13, len(anthologies))
        self.assertEquals(12, len(anthologies[0].works.all()))

    def test_fake_series(self):
        series = self.ourchive_fakes.generate_series(models.User.objects.all().first().id, 30, True, **{'token': 'untitled'})
        self.assertEquals(30, len(series))