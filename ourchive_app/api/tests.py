from django.test import TestCase
from rest_framework.test import force_authenticate, APIRequestFactory
import api.models as models
import api.views as api_views
from django.core.management import call_command


class ApiTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        fixtures = [
            'tagtype', 'tags', 'worktype', 'work', 'bookmark', 'bookmarkcollection', 'chapter', 'ourchivesettings'
        ]
        cls.test_user = models.User.objects.create(username="test_user")
        cls.test_admin_user = models.User.objects.create(username="test_admin_user")
        for db_name in cls._databases_names(include_mirrors=False):
            call_command("loaddata", *fixtures, verbosity=0, database=db_name)

    def test_can_view_notifications(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.UserNotificationList.as_view()
        request = factory.get(f'/username/{user.username}/notifications')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEquals(response.status_code, 200)

    def test_can_view_subscriptions(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.UserSubscriptionList.as_view()
        request = factory.get(f'/username/{user.username}/subscriptions')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEquals(response.status_code, 200)

    def test_can_view_account(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.UserDetail.as_view()
        request = factory.get(f'/users/{user.id}/')
        force_authenticate(request, user=user)
        response = view(request, pk=user.id)
        self.assertEquals(response.status_code, 200)

    def test_can_view_works(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.WorkList.as_view()
        request = factory.get(f'/works')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEquals(response.status_code, 200)

    def test_can_update_works(self):
        work_update_json = {
            "tags": [],
            "id": 1,
            "word_count": 0,
            "audio_length": 0,
            "attributes": [],
            "chapter_count": 0,
            "work_type_name": "Podfic",
            "uid": "337c44d8-71b1-4ae7-94a4-65285d955eec",
            "title": "Untitled Work",
            "summary": "",
            "notes": "",
            "is_complete": False,
            "anon_comments_permitted": False,
            "comments_permitted": False,
            "fingerguns": 1,
            "draft": False,
            "comment_count": 0,
        }
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        work = models.Work.objects.get(id=1)
        view = api_views.WorkDetail.as_view()
        request = factory.patch(f'/works/1/', work_update_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request, pk=1)
        # test_user doesn't own work id=1
        self.assertEquals(response.status_code, 403)
        force_authenticate(request, user=self.test_admin_user)
        response = view(request, pk=1)
        self.assertEquals(response.status_code, 200)

    def test_can_view_bookmarks(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.BookmarkList.as_view()
        request = factory.get(f'/bookmarks')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEquals(response.status_code, 200)

    def test_can_update_bookmarks(self):
        bookmark_update_json = {
            "work_id": 1,
            "collection": None,
            "id": 1,
            "tags": [],
            "attributes": [],
            "title": "ok ok",
            "rating": 0,
            "description": "<p>hello</p>",
            "created_on": "2023-08-14T14:32:14.349520Z",
            "updated_on": "2023-08-14T14:32:14.362771Z",
            "draft": False,
            "anon_comments_permitted": True,
            "comments_permitted": True,
            "comment_count": 0,
            "public_notes": None,
            "private_notes": None,
            "is_private": False
        }
        factory = APIRequestFactory()
        view = api_views.BookmarkDetail.as_view()
        request = factory.patch(
            f'/bookmarks/1/', bookmark_update_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request, pk=1)
        # test_user doesn't own bookmark id=1
        self.assertEquals(response.status_code, 403)
        force_authenticate(request, user=self.test_admin_user)
        response = view(request, pk=1)
        self.assertEquals(response.status_code, 200)

    def test_can_view_collections(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.BookmarkCollectionList.as_view()
        request = factory.get(f'/bookmarkcollections')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEquals(response.status_code, 200)

    def test_can_update_collections(self):
        collection_update_json = {
            "id": 1,
            "tags": [],
            "attributes": [],
            "bookmarks_readonly": [],
            "bookmarks": [],
            "uid": "b93f1427-98b0-4554-87e1-25e911b09774",
            "title": "New Bookmark Collection",
            "is_complete": False,
            "header_url": None,
            "header_alt_text": None,
            "short_description": "does what it says on the tin",
            "description": "",
            "created_on": "2023-08-14T14:32:22.792308Z",
            "updated_on": "2023-08-14T14:32:22.803361Z",
            "draft": False,
            "anon_comments_permitted": True,
            "comments_permitted": True,
            "comment_count": 0,
            "is_private": False
        }
        factory = APIRequestFactory()
        view = api_views.BookmarkCollectionDetail.as_view()
        request = factory.patch(
            f'/bookmarkcollections/1/', collection_update_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request, pk=1)
        # test_user doesn't own collection id=1
        self.assertEquals(response.status_code, 403)
        force_authenticate(request, user=self.test_admin_user)
        response = view(request, pk=1)
        self.assertEquals(response.status_code, 200)

    def test_can_view_import_statuses(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.ImportStatus.as_view()
        request = factory.get(f'/users/{user.id}/importstatus')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEquals(response.status_code, 200)

    def test_can_create_fingerguns(self):
        fingerguns_create_json = {
            "work": 1,
        }
        factory = APIRequestFactory()
        view = api_views.FingergunList.as_view()
        request = factory.post(
            f'/fingerguns/', fingerguns_create_json, format='json')
        response = view(request)
        # anon fingerguns are allowed
        self.assertEquals(response.status_code, 201)
        fingerguns_create_json['user'] = 'test_user'
        request = factory.post(
            f'/fingerguns/', fingerguns_create_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request)
        self.assertEquals(response.status_code, 201)
        created_fingergun_id = response.data['id']
        created_fingergun = models.Fingergun.objects.get(id=created_fingergun_id)
        self.assertEquals(created_fingergun.user.id, 1)
        self.assertEquals(created_fingergun.work.id, 1)
