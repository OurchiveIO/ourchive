from django.test import TestCase
from rest_framework.test import APIClient

class UserProfileViewTests(TestCase):
	client = APIClient()
	fixtures = ['user', 'tagtype', 'tag', 'worktype', 'work', 'bookmark', 'bookmarklink', 
				'bookmarkcomment', 'chapter', 'chaptercomment',
				'fingergun', 'userblocks', 'userprofile', 'ourchivesetting']

	def user_profile_default_content_work_shows_works(self):
		assert False

	def user_profile_default_content_bookmark_shows_bookmarks(self):
		assert False

	def user_profile_default_content_null_shows_index_0(self):
		assert False