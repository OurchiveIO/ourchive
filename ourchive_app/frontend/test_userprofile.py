from django.test import TestCase
from rest_framework.test import APIClient

class UserViewTests(TestCase):
	fixtures = ['user', 'tagtype', 'tag', 'worktype', 'work', 'bookmark', 'bookmarklink', 
				'bookmarkcomment', 'chapter', 'chaptercomment',
				'fingergun', 'userblocks', 'ourchivesetting']

	def test_user_profile_shows_works(self):
		response = self.client.get("/username/imp/works/")
		response_content = str(response.content)
		self.assertIn('user_works_header', response_content)

	def test_user_profile_shows_bookmarks(self):
		response = self.client.get("/username/imp/bookmarks/")
		response_content = str(response.content)
		self.assertIn('user_bookmarks_header', response_content)