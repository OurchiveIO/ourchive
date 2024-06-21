from unittest import skip

from django.test import TestCase
import core.models as models
from ourchive_app.util.ourchive_fakes import OurchiveFakes
from ourchive_app.util import ourchive_fixtures


class CoreTests(TestCase):
    fixtures = ['ourchivesettings', 'notificationtype']

    @classmethod
    def setUpTestData(cls):
        cls.ourchive_fakes = OurchiveFakes()
        cls.ourchive_fakes.generate_users(20, True)
        cls.ourchive_fakes.generate_languages([], True)
        cls.ourchive_fakes.generate_attribute_types(4, True)
        cls.ourchive_fakes.generate_attributes(10, True)
        cls.ourchive_fakes.generate_tag_types(4, True)
        cls.ourchive_fakes.generate_tags(20, True)
        cls.attributes_generated = False

    def test_fake_users(self):
        users = models.User.objects.all()
        self.assertEquals(20, len(users))

    def test_fake_works(self):
        works = self.ourchive_fakes.generate_works_and_chapters(models.User.objects.all().first().id,
                                                                30, True, 5,
                                                                **{'token': 'untitled'})[0]
        self.assertEquals(30, len(works))
        self.assertEquals(5, len(works[0].chapters.all()))

    def test_fake_bookmarks(self):
        bookmarks = self.ourchive_fakes.generate_bookmarks(models.User.objects.all().first().id, 30, True,
                                                           **{'token': 'untitled'})
        self.assertEquals(30, len(bookmarks))

    def test_fake_tags(self):
        tags = self.ourchive_fakes.generate_tags(30, True, **{'token': 'untitled', 'create_tag_types': True})
        self.assertEquals(30, len(tags))

    def test_fake_attributes(self):
        attributes = self.ourchive_fakes.generate_attributes(32, False,
                                                             **{'token': 'untitled',
                                                                'create_attribute_types': False,
                                                                'attribute_type_count': 11})
        self.assertEquals(32, len(attributes))
        self.assertEquals(models.AttributeType.objects.count(), 4)

    def test_fake_works_no_save(self):
        works_and_chapters = self.ourchive_fakes.generate_works_and_chapters(models.User.objects.all().first().id, 30,
                                                                             False, 5)
        self.assertEquals(30, len(works_and_chapters[0]))
        self.assertEquals(150, len(works_and_chapters[1]))

    def test_fake_work_types(self):
        type_names = ['Fic', 'Vid', 'Podfic', 'Art']
        types = self.ourchive_fakes.generate_work_types(True, **{'type_names': type_names})
        self.assertEquals(4, len(types))
        self.assertIsNotNone(models.WorkType.objects.filter(type_name=type_names[1]).first().id)


    def test_fake_collections(self):
        collections_opts = {
            'assign_works': False,
            'create_works': True,
            'works_count': 10,
            'assign_tags': True,
            'tags_count': 20,
            'assign_attributes': True,
            'attributes_count': 10,
            'create_languages': False
        }
        collections = self.ourchive_fakes.generate_collections(
            models.User.objects.all().first().id,
            20,
            True,
            **collections_opts
        )
        self.assertEquals(20, len(collections))
        self.assertEquals(10, len(collections[0].works.all()))

    def test_fake_collections_with_varying_users(self):
        collections_opts = {
            'create_works': True,
            'works_count': 10,
            'assign_tags': True,
            'tags_count': 20,
            'assign_attributes': True,
            'attributes_count': 10,
            'create_languages': False,
            'persist_db': True,
            'chapter_count': 2,
            'token': 'untitled',
            'obj_count': 20
        }
        users = self.ourchive_fakes.generate_users(2, True)
        collections = self.ourchive_fakes.generate_collections_with_varying_users(users, len(users), **collections_opts)
        self.assertEquals(40, len(collections))

    def test_fake_multiuser_collections(self):
        collections_opts = {
            'assign_works': False,
            'create_works': True,
            'works_count': 10,
            'assign_tags': True,
            'tags_count': 20,
            'assign_attributes': True,
            'attributes_count': 10,
            'assign_languages': True,
            'user_count': 3
        }
        collections = self.ourchive_fakes.generate_collections_with_cocreators(20, **collections_opts)
        self.assertEquals(20, len(collections))
        self.assertEquals(3, len(collections[0].users.all()))

    def test_fake_multiuser_works(self):
        works = self.ourchive_fakes.generate_works_with_cocreators(5, **{'user_count': 2})
        self.assertEquals(5, len(works))
        self.assertEquals(2, len(works[0].users.all()))

    def test_fake_multi_owner_anthologies(self):
        anthologies = self.ourchive_fakes.generate_anthologies_with_cocreators(10, **{'user_count': 6})
        self.assertEquals(10, len(anthologies))
        self.assertEquals(6, len(anthologies[0].owners.all()))

    def test_settings_choices(self):
        settings_choices = models.Settings.choices
        self.assertIsNotNone(settings_choices)

    def test_fake_anthologies(self):
        anthologies_opts = {
            'create_works': True,
            'works_count': 12,
            'assign_tags': True,
            'tags_count': 15,
            'assign_attributes': True,
            'attributes_count': 13,
            'assign_languages': True
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
        series = self.ourchive_fakes.generate_series(models.User.objects.all().first().id, 30, True,
                                                     **{'token': 'untitled'})
        self.assertEquals(30, len(series))

    def test_fake_chapter_comments(self):
        comments = self.ourchive_fakes.generate_chapter_comments(models.User.objects.all().first().id, 10, True,
                                                                 None,
                                                                 **{'reply_max': 5, 'user_count': 3,
                                                                    'create_users': False,
                                                                    'comment_depth': 2})
        self.assertEquals(10, len(comments))

    def test_fake_collection_comments(self):
        comments = self.ourchive_fakes.generate_collection_comments(models.User.objects.all().first().id, 10, True,
                                                                    None,
                                                                    **{'reply_max': 5, 'user_count': 3,
                                                                       'create_users': False,
                                                                       'comment_depth': 2})
        self.assertEquals(10, len(comments))

    def test_fake_announcements(self):
        announcements = self.ourchive_fakes.generate_announcements(25, True)
        self.assertEquals(25, len(announcements))

    def test_fake_news(self):
        news = self.ourchive_fakes.generate_news(15, True)
        self.assertEquals(15, len(news))

    def test_generate_everything(self):
        self.ourchive_fakes.generate_everything(5, '', False)
        self.assertEquals(25, models.Work.objects.count())

    def test_get_settings(self):
        objects_added = ourchive_fixtures.load_data("ourchive_app/core/fixtures/", "required_data.yaml")
        self.assertEquals(14, objects_added)
