from django.test import TestCase
import api.models as models
from ourchive_app.util.ourchive_fakes import OurchiveFakes

class CoreTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ourchive_fakes = OurchiveFakes()
        cls.ourchive_fakes.generate_users(20, True)

    def test_fake_users(self):
        users = models.User.objects.all()
        self.assertEquals(20, len(users))

    def test_fake_works(self):
        works = self.ourchive_fakes.generate_works(models.User.objects.all().first().id, 30, True, 5)
        self.assertEquals(30, len(works))
        self.assertEquals(5, len(works[0].chapters.all()))