from django.test import TestCase
from rest_framework.test import APIClient

class BookmarkViewTests(TestCase):
	client = APIClient()
	fixtures = ['user', 'tagtype', 'tag', 'bookmark', 'worktype', 'work', 'bookmarklink', 
				'bookmarkcomment', 'userprofile', 'ourchivesetting']

	def test_get_bookmarks(self):
		assert False

	def test_get_draft_bookmark_as_owner(self):
		assert False

	def test_get_draft_bookmark_as_nonowner(self):
		assert False

	def test_edit_bookmark_as_owner(self):
		assert False

	def test_create_bookmark(self):
		assert False

	def test_create_bookmark_no_title(self):
		assert False

	def test_edit_bookmark_as_nonowner(self):
		assert False

	def test_delete_bookmark_as_owner(self):
		assert False

	def test_delete_bookmark_as_nonowner(self):
		assert False

	def test_bookmark_comment(self):
		assert False

	def test_edit_bookmark_comment_as_owner(self):
		assert False

	def test_edit_bookmark_comment_as_nonowner(self):
		assert False

	def test_delete_bookmark_comment_as_owner(self):
		assert False

	def test_delete_bookmark_comment_as_nonowner(self):
		assert False

	def test_logged_in_user_post_comment_on_limited_bookmark(self):
		assert False

	def test_anon_user_post_comment_on_limited_bookmark(self):
		assert False

	def test_logged_in_user_post_comment_on_everyone_bookmark(self):
		assert False

	def test_anon_user_post_comment_on_everyone_bookmark(self):
		assert False

	def test_logged_in_user_post_comment_on_none_bookmark(self):
		assert False

	def test_anon_user_post_comment_on_none_bookmark(self):
		assert False