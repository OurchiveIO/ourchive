from django.test import TestCase
from rest_framework.test import force_authenticate, APIRequestFactory
import api.models as models
import api.views as api_views
from django.core.management import call_command
from api.utils import count_words
from unittest import skip


class ApiTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        fixtures = [
            'tagtype', 'tags', 'worktype', 'work', 'bookmark', 'bookmarkcollection', 'chapter', 'ourchivesettings'
        ]
        cls.test_user = models.User.objects.create(
            username="test_user", email="test_user@test.com")
        cls.test_admin_user = models.User.objects.create(
            username="test_admin_user", email="test_admin@test.com")
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

    def test_parse_work_url(self):
        from etl.ao3 import util
        expected_id = '33568501'
        work_multichapter_url = 'https://archiveofourown.org/works/33568501/chapters/83411257'
        work_single_url = 'https://archiveofourown.org/works/33568501'
        work_single_url_trailing = 'https://archiveofourown.org/works/33568501/'
        work_view_full_url = 'https://archiveofourown.org/works/33568501?view_full_work=true'
        plain_id = '33568501'
        work_id = util.parse_work_id_from_ao3_url(work_multichapter_url)
        self.assertEquals(expected_id, work_id)
        work_id = util.parse_work_id_from_ao3_url(work_single_url)
        self.assertEquals(expected_id, work_id)
        work_id = util.parse_work_id_from_ao3_url(work_single_url_trailing)
        self.assertEquals(expected_id, work_id)
        work_id = util.parse_work_id_from_ao3_url(work_view_full_url)
        self.assertEquals(expected_id, work_id)
        work_id = util.parse_work_id_from_ao3_url(plain_id)
        self.assertEquals(expected_id, work_id)

    @skip
    def test_work_drafts_not_in_search(self):
        work_draft_json = {
            "tags": [],
            "word_count": 0,
            "audio_length": 0,
            "attributes": [],
            "chapter_count": 0,
            "work_type_name": "Fic",
            "title": "My BTVS draft WIP",
            "summary": "Buffy and Faith go for a nice walk, and nothing bad happens.",
            "notes": "",
            "is_complete": False,
            "anon_comments_permitted": False,
            "comments_permitted": False,
            "fingerguns": 1,
            "draft": True,
            "comment_count": 0,
            "user": "test_user"
        }
        work_nondraft_json = {
            "tags": [],
            "word_count": 0,
            "audio_length": 0,
            "attributes": [],
            "chapter_count": 0,
            "work_type_name": "Fic",
            "title": "My BTVS fic",
            "summary": "Buffy and Faith go for a nice walk, and several bad things happen.",
            "notes": "",
            "is_complete": False,
            "anon_comments_permitted": False,
            "comments_permitted": False,
            "draft": False,
            "comment_count": 0,
            "user": "test_user"
        }
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        work = models.Work.objects.get(id=1)
        view = api_views.WorkList.as_view()
        request = factory.post(f'/works/', work_draft_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request)
        request = factory.post(f'/works/', work_nondraft_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request)
        search_view = api_views.SearchList.as_view()
        work_search_data = {
            "work_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "bookmark_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "collection_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "tag_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "user_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            }
        }
        request = factory.post(f'/search/', work_search_data, format='json')
        force_authenticate(request, user=self.test_user)
        response = search_view(request)
        works = response.data['results']['work']['data']
        self.assertEquals(1, len(works))
        self.assertEquals("My BTVS fic", works[0]['title'])

    @skip
    def test_bookmark_drafts_not_in_search(self):
        bookmark_draft_json = {
            "work_id": 1,
            "collection": None,
            "tags": [],
            "attributes": [],
            "title": "DRAFT - BTVS",
            "rating": 0,
            "description": "<p>hello</p>",
            "draft": True,
            "anon_comments_permitted": True,
            "comments_permitted": True,
            "comment_count": 0,
            "public_notes": None,
            "private_notes": None,
            "is_private": False,
            "user": "test_user"
        }
        bookmark_nondraft_json = {
            "work_id": 1,
            "collection": None,
            "tags": [],
            "attributes": [],
            "title": "NOT A DRAFT - BTVS",
            "rating": 0,
            "description": "<p>hello</p>",
            "draft": False,
            "anon_comments_permitted": True,
            "comments_permitted": True,
            "comment_count": 0,
            "public_notes": None,
            "private_notes": None,
            "is_private": False,
            "user": "test_user"
        }
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.BookmarkList.as_view()
        request = factory.post(f'/bookmarks/', bookmark_draft_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request)
        request = factory.post(f'/bookmarks/', bookmark_nondraft_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request)
        search_view = api_views.SearchList.as_view()
        bookmark_search_data = {
            "work_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "bookmark_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "collection_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "tag_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "user_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            }
        }
        request = factory.post(f'/search/', bookmark_search_data, format='json')
        force_authenticate(request, user=self.test_user)
        response = search_view(request)
        bookmarks = response.data['results']['bookmark']['data']
        self.assertEquals(1, len(bookmarks))
        self.assertEquals("NOT A DRAFT - BTVS", bookmarks[0]['title'])

    @skip
    def test_collection_drafts_not_in_search(self):
        collection_draft_json = {
            "tags": [],
            "attributes": [],
            "bookmarks_readonly": [],
            "bookmarks": [],
            "title": "MY DRAFT COLLECTION - BTVS",
            "is_complete": False,
            "header_url": None,
            "header_alt_text": None,
            "short_description": "does what it says on the tin",
            "description": "",
            "draft": True,
            "anon_comments_permitted": True,
            "comments_permitted": True,
            "comment_count": 0,
            "is_private": False,
            "user": "test_user"
        }
        collection_nondraft_json = {
            "tags": [],
            "attributes": [],
            "bookmarks_readonly": [],
            "bookmarks": [],
            "title": "NOT A DRAFT - BTVS",
            "is_complete": False,
            "header_url": None,
            "header_alt_text": None,
            "short_description": "does what it says on the tin",
            "description": "",
            "draft": False,
            "anon_comments_permitted": True,
            "comments_permitted": True,
            "comment_count": 0,
            "is_private": False,
            "user": "test_user"
        }
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.BookmarkCollectionList.as_view()
        request = factory.post(f'/bookmarkcollections/',
                               collection_draft_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request)
        request = factory.post(f'/bookmarkcollections/',
                               collection_nondraft_json, format='json')
        force_authenticate(request, user=self.test_user)
        response = view(request)
        search_view = api_views.SearchList.as_view()
        collection_search_data = {
            "work_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "bookmark_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "collection_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "tag_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            },
            "user_search": {
                "include_filter": {},
                "exclude_filter": {},
                "term": "btvs",
                "order_by": "created_on",
                "page": 1
            }
        }
        request = factory.post(f'/search/', collection_search_data, format='json')
        force_authenticate(request, user=self.test_user)
        response = search_view(request)
        collections = response.data['results']['collection']['data']
        self.assertEquals(1, len(collections))
        self.assertEquals("NOT A DRAFT - BTVS", collections[0]['title'])

    def test_cannot_view_nonowned_draft_work(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.WorkDetail.as_view()
        request = factory.get(f'/works/2/')
        force_authenticate(request, user=user)
        response = view(request, pk=2)
        self.assertEquals(response.status_code, 404)

    def test_cannot_view_nonowned_draft_chapter(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.ChapterDetail.as_view()
        request = factory.get(f'/chapters/2/')
        force_authenticate(request, user=user)
        response = view(request, pk=2)
        self.assertEquals(response.status_code, 404)

        user = models.User.objects.get(username='test_admin_user')
        view = api_views.ChapterDetail.as_view()
        request = factory.get(f'/chapters/2/')
        force_authenticate(request, user=user)
        response = view(request, pk=2)
        self.assertEquals(response.status_code, 200)

    def test_cannot_view_nonowned_draft_bookmark(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.BookmarkDetail.as_view()
        request = factory.get(f'/bookmarks/2/')
        force_authenticate(request, user=user)
        response = view(request, pk=2)
        self.assertEquals(response.status_code, 404)

        request = factory.get(f'/bookmarks/3/')
        force_authenticate(request, user=user)
        response = view(request, pk=3)
        self.assertEquals(response.status_code, 200)

    def test_cannot_view_nonowned_draft_collection(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.BookmarkCollectionDetail.as_view()
        request = factory.get(f'/bookmarkcollections/2/')
        force_authenticate(request, user=user)
        response = view(request, pk=2)
        self.assertEquals(response.status_code, 404)

    def test_can_view_owned_draft_work(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.WorkDetail.as_view()
        request = factory.get(f'/works/3/')
        force_authenticate(request, user=user)
        response = view(request, pk=2)
        self.assertEquals(response.status_code, 404)

    def test_can_view_owned_draft_collection(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.BookmarkCollectionDetail.as_view()
        request = factory.get(f'/bookmarkcollections/3/')
        force_authenticate(request, user=user)
        response = view(request, pk=3)
        self.assertEquals(response.status_code, 200)

    def test_cannot_register_with_reg_disabled(self):
        factory = APIRequestFactory()
        view = api_views.UserList.as_view()
        require_invite = models.OurchiveSetting.objects.filter(
            name='Invite Only').first()
        require_invite.value = "False"
        require_invite.save()
        reg_permit = models.OurchiveSetting.objects.filter(
            name='Registration Permitted').first()
        reg_permit.value = "False"
        reg_permit.save()
        user_data = {
            "username": "test_new_user",
            "email": "test@test.com",
            "password": "changem3r1ghtn0w",
            "profile": "",
            "icon": "",
            "icon_alt_text": "",
            "has_notifications": False,
            "default_content": "Work",
            "attributes": [],
            "cookies_accepted": True,
            "can_upload_audio": True,
            "can_upload_export_files": True,
            "can_upload_images": True,
            "default_work_type": "Fic",
            "collapse_chapter_image": True,
            "collapse_chapter_audio": False,
            "collapse_chapter_text": True
        }
        request = factory.post(f'/users/', user_data, format='json')
        response = view(request)
        self.assertEquals(response.status_code, 403)

    def test_can_register_with_reg_enabled(self):
        factory = APIRequestFactory()
        view = api_views.UserList.as_view()
        require_invite = models.OurchiveSetting.objects.filter(
            name='Invite Only').first()
        require_invite.value = "False"
        require_invite.save()
        reg_permit = models.OurchiveSetting.objects.filter(
            name='Registration Permitted').first()
        reg_permit.value = "True"
        reg_permit.save()
        user_data = {
            "username": "test_new_user",
            "email": "test@test.com",
            "password": "changem3r1ghtn0w",
            "profile": "",
            "icon": "",
            "icon_alt_text": "",
            "has_notifications": False,
            "default_content": "Work",
            "attributes": [],
            "cookies_accepted": True,
            "can_upload_audio": True,
            "can_upload_export_files": True,
            "can_upload_images": True,
            "default_work_type": "Fic",
            "collapse_chapter_image": True,
            "collapse_chapter_audio": False,
            "collapse_chapter_text": True
        }
        request = factory.post(f'/users/', user_data, format='json')
        response = view(request)
        self.assertEquals(response.status_code, 201)

    def test_can_request_invite(self):
        invite_request = {
            "email": "test@test.com",
            "join_reason": "Curiosity"
        }
        factory = APIRequestFactory()
        view = api_views.Invitations.as_view()
        request = factory.post(f'/invitations/', invite_request, format='json')
        response = view(request)
        self.assertEquals(response.status_code, 200)
        new_user = models.User.objects.create(
            username="test_user_2", email="test@test.com")
        request = factory.post(f'/invitations/', invite_request, format='json')
        response = view(request)
        self.assertEquals(response.status_code, 418)

    def test_cannot_view_user_email(self):
        factory = APIRequestFactory()
        user = models.User.objects.get(username='test_user')
        view = api_views.UserDetail.as_view()
        request = factory.get(f'/users/{user.id}/')
        force_authenticate(request, user=user)
        response = view(request, pk=user.id)
        email_response = response.data['email']
        self.assertEquals('test_user@test.com', email_response)
        request = factory.get(f'/users/2/')
        force_authenticate(request, user=user)
        response = view(request, pk=2)
        email_response = response.data['email']
        self.assertEquals(None, email_response)

    def test_new_chapter_word_count(self):
        work = models.Work.objects.get(id=1)
        chapter = models.Chapter()
        chapter.text = "The quick brown fox jumped over the lazy dog"
        chapter.work = work
        chapter.user_id = 1
        chapter.save()
        self.assertEquals(9, chapter.word_count)

    def test_updated_chapter_word_count(self):
        chapter = models.Chapter.objects.get(id=1)
        chapter.text = "The quick brown fox jumped over the lazy dog"
        chapter.save()
        self.assertEquals(9, chapter.word_count)

    def test_word_count_util(self):
        test_string = """
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Nisl condimentum id venenatis a condimentum vitae sapien pellentesque. Eget duis at tellus at urna condimentum. Faucibus interdum posuere lorem ipsum dolor sit amet consectetur adipiscing. A iaculis at erat pellentesque adipiscing commodo elit at. Velit laoreet id donec ultrices tincidunt arcu non. Turpis massa sed elementum tempus egestas sed sed "risus" pretium. Ridiculus mus mauris vitae ultricies leo integer. Ut pharetr'a sit-amet aliquam id diam maecenas'ultricies. Bibendum arcu vitae elementum curabitur vitae. Sed libero enim sed faucibus. Donec enim diam vulputate ut pharetra sit. Viverra nibh cras pulvinar mattis nunc sed blandit libero. Lobortis feugiat vivamus at augue eget arcu dictum varius. Nec sagittis aliquam malesuada bibendum arcu. Leo duis ut diam quam. Bibendum est ultricies integer quis auctor elit sed vulputate. Luctus accumsan tortor posuere ac ut.
        """
        word_count = count_words(test_string)
        self.assertEquals(148, word_count)

    def test_search_tag_include_facet(self):
        test_request = {
            "work_search": {
                "term": "untitled",
                "include_mode": "all",
                "exclude_mode": "all",
                "page": 1,
                "order_by": "-updated_on",
                "include_filter": {
                    "tags": ["buffy the vampire slayer"],
                    "attributes": [],
                    "Work Word Count": ["word_count_gte", "word_count_lte"],
                    "Completion Status": []
                },
                "exclude_filter": {
                    "tags": [],
                    "attributes": [],
                    "Work Word Count": ["word_count_gte", "word_count_lte"]
                }
            },
            "bookmark_search": {
                "term": "untitled",
                "include_mode": "all",
                "exclude_mode": "all",
                "page": 1,
                "order_by": "-updated_on",
                "include_filter": {
                    "tags": ["buffy the vampire slayer"],
                    "attributes": [],
                    "Work Word Count": ["word_count_gte", "word_count_lte"],
                    "Completion Status": []
                },
                "exclude_filter": {
                    "tags": [],
                    "attributes": [],
                    "Work Word Count": ["word_count_gte", "word_count_lte"]
                }
            },
            "collection_search": {
                "term": "untitled",
                "include_mode": "all",
                "exclude_mode": "all",
                "page": 1,
                "order_by": "-updated_on",
                "include_filter": {
                    "tags": ["buffy the vampire slayer"],
                    "attributes": [],
                    "Work Word Count": ["word_count_gte", "word_count_lte"],
                    "Completion Status": []
                },
                "exclude_filter": {
                    "tags": [],
                    "attributes": [],
                    "Work Word Count": ["word_count_gte", "word_count_lte"]
                }
            },
            "user_search": {
                "term": "untitled",
                "include_mode": "all",
                "exclude_mode": "all",
                "page": 1,
                "order_by": "-updated_on",
                "include_filter": {"tags": [], "attributes": []},
                "exclude_filter": {"tags": [], "attributes": []}
            },
            "tag_search": {
                "term": "untitled",
                "include_mode": "all",
                "exclude_mode": "all",
                "page": 1,
                "order_by": "-updated_on",
                "include_filter": {"tag_type": [], "text": []},
                "exclude_filter": {"tag_type": [], "text": []}
            }
        }
        factory = APIRequestFactory()
        view = api_views.SearchList.as_view()
        request = factory.post(f'/search/', test_request, format='json')
        response = view(request)
        self.assertEquals(response.status_code, 200)
        facets = response.data['results']['include_facets']
        facet_found = False
        for facet in facets:
            if facet['label'] == 'Fandom':
                for value in facet['values']:
                    if value['label'] == 'Buffy the Vampire Slayer':
                        self.assertEquals(value['checked'], True)
                        facet_found = True
        self.assertEquals(facet_found, True)
