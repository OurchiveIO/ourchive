from django.test import TestCase
from rest_framework.test import APIClient

class UserBlockViewTests(TestCase):
	client = APIClient()
	fixtures = ['user', 'tagtype', 'tag', 'worktype', 'work', 'bookmark', 'bookmarklink', 
				'bookmarkcomment', 'chapter', 'chaptercomment',
				'fingergun', 'userblocks', 'userprofile', 'ourchivesetting']

	def blocked_user_comment_on_work(self):
		assert False

	def nonblocked_user_comment_on_work(self):
		assert False

	def blocked_user_comment_on_bookmark(self):
		assert False

	def nonblocked_user_comment_on_bookmark(self):
		assert False