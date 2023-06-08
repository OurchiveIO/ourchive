from django.test import TestCase
from rest_framework.test import APIClient

class WorkViewTests(TestCase):
	client = APIClient()
	fixtures = ['user', 'tagtype', 'tag', 'worktype', 'work', 'bookmark', 'bookmarklink', 
				'bookmarkcomment', 'chapter', 'chaptercomment', 'notificationtype', 'notification', 
				'fingergun', 'userblocks', 'ourchivesetting']

	def test_get_works(self):
		assert False

	def test_get_draft_work_as_owner(self):
		assert False

	def test_get_draft_work_as_nonowner(self):
		assert False

	def test_edit_work_as_owner(self):
		assert False

	def test_edit_work_as_nonowner(self):
		assert False

	def test_get_chapter(self):
		assert False

	def test_get_draft_chapter_as_owner(self):
		assert False

	def test_get_draft_chapter_as_nonowner(self):
		assert False

	def test_create_work(self):
		assert False

	def test_create_chapter(self):
		assert False

	def test_edit_chapter_as_owner(self):
		assert False

	def test_edit_chapter_as_nonowner(self):
		assert False

	def test_create_work(self):
		assert False

	def test_edit_work(self):
		assert False

	def test_add_tag_to_work(self):
		assert False

	def test_change_chapter_number(self):
		assert False

	def test_delete_work_as_owner(self):
		assert False

	def test_delete_chapter_as_owner(self):
		assert False

	def test_delete_work_as_nonowner(self):
		assert False

	def test_delete_chapter_as_nonowner(self):
		assert False

	def test_chapter_comment(self):
		assert False

	def test_edit_chapter_comment_as_owner(self):
		assert False

	def test_edit_chapter_comment_as_nonowner(self):
		assert False

	def test_delete_chapter_comment_as_owner(self):
		assert False

	def test_delete_chapter_comment_as_nonowner(self):
		assert False

	def test_fingergun_work(self):
		assert False