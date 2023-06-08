from django.test import TestCase
from rest_framework.test import APIClient

from unittest import skip
@skip
class UserBlockViewTests(TestCase):
	client = APIClient()
	fixtures = ['user', 'tagtype', 'tag', 'worktype', 'work', 'bookmark', 'bookmarklink', 
				'bookmarkcomment', 'chapter', 'chaptercomment',
				'fingergun', 'userblocks', 'ourchivesetting']

	def test_blocked_user_comment_on_work(self):
		assert False

	def test_nonblocked_user_comment_on_work(self):
		assert False

	def test_blocked_user_comment_on_bookmark(self):
		assert False

	def test_nonblocked_user_comment_on_bookmark(self):
		assert False