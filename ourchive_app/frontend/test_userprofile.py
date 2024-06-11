from django.test import TestCase
from rest_framework.test import APIClient
import api.models as models
from django.core.management import call_command

class UserViewTests(TestCase):

	@classmethod
	def setUpTestData(cls):
		# Set up data for the whole TestCase
		fixtures = [
		    'tagtype', 'tags', 'worktype', 'work', 'bookmark', 'bookmarkcollection', 'chapter', 'ourchivesettings'
		]
		cls.test_user = models.User.objects.create(username="test_user", email="test_user@test.com")
		cls.test_admin_user = models.User.objects.create(username="test_admin_user", email="test_admin@test.com")
		for db_name in cls._databases_names(include_mirrors=False):
			call_command("loaddata", *fixtures, verbosity=0, database=db_name)

	def test_user_profile_shows_works(self):
		response = self.client.get("/username/imp/works/")
		response_content = str(response.content)
		self.assertIn('user_works_header', response_content)

	def test_user_profile_shows_bookmarks(self):
		response = self.client.get("/username/imp/bookmarks/")
		response_content = str(response.content)
		self.assertIn('user_bookmarks_header', response_content)