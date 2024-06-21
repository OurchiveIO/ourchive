from django.test import TestCase
from rest_framework.test import APIClient
import core.models as models
from django.core.management import call_command

class UserViewTests(TestCase):

	@classmethod
	def setUpTestData(cls):
		cls.test_user = models.User.objects.create(username="test_user", email="test_user@test.com")
		cls.test_admin_user = models.User.objects.create(username="test_admin_user", email="test_admin@test.com")

	def test_user_profile_shows_works(self):
		pass

	def test_user_profile_shows_bookmarks(self):
		pass