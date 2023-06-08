from django.test import TestCase
from rest_framework.test import APIClient

from unittest import skip
@skip
class NotificationViewTests(TestCase):
	client = APIClient()
	fixtures = ['user', 'notificationtype', 'notification', 'ourchivesetting']

	def test_load_notifications(self):
		assert False

	def test_delete_notification_as_owner(self):
		assert False

	def test_delete_notification_as_nonowner(self):
		assert False

	def test_mark_read_notification_as_owner(self):
		assert False

	def test_mark_read_notification_as_nonowner(self):
		assert False