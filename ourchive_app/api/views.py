from django.contrib.auth.models import Group
from rest_framework import viewsets, generics, permissions
from api.serializers import *
from api.models import *
from api.permissions import *
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser
from .search.search_service import OurchiveSearch
from .search.search_obj import GlobalSearch
from django.db.models import Q
import datetime
from django.utils.crypto import get_random_string
from django.conf import settings
import html
from .file_helpers import FileHelperService
from django.core.exceptions import ObjectDoesNotExist
import nh3
from . import work_export
from django.contrib.auth.models import AnonymousUser
from etl import ao3
import threading
from etl.models import WorkImport, ChiveExport
from etl.ao3 import util
from .utils import get_star_count
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from django.db.models import Count
from api.custom_pagination import NonPaginatedResultSetPagination
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'works': reverse('work-list', request=request, format=format),
        'chapters': reverse('chapter-list', request=request, format=format),
        'tagtypes': reverse('tag-type-list', request=request, format=format),
        'tags': reverse('tag-list', request=request, format=format),
        'worktypes': reverse('work-type-list', request=request, format=format),
        'bookmarks': reverse('bookmark-list', request=request, format=format),
        'bookmarkcollections': reverse('bookmark-collection-list', request=request, format=format),
        'messages': reverse('message-list', request=request, format=format),
        'notifications': reverse('notification-list', request=request, format=format),
        'notificationtypes': reverse('notification-type-list', request=request, format=format),
        'settings': reverse('ourchive-setting-list', request=request, format=format),
        'searchresults': reverse('search-list', request=request, format=format),
        'fingerguns': reverse('fingergun-list', request=request, format=format),
        'userblocks': reverse('user-blocks-list', request=request, format=format),
        'tag-autocomplete': reverse('tag-autocomplete', request=request, format=format),
        'attributetypes': reverse('attribute-type-list', request=request, format=format),
        'attributevalues': reverse('attribute-value-list', request=request, format=format),
    })


class SearchList(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        searcher = OurchiveSearch()
        results = searcher.do_search(**request.data)
        return Response({'results': results})

    def get(self, request, format=None):
        return Response(GlobalSearch().to_dict())

    def get_queryset(self):
        searcher = OurchiveSearch()
        return searcher.do_search(**self.kwargs)


class RegistrationUtils(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        username = request.GET.get('username')
        if User.objects.filter(username=username).exists():
            return Response({'exists': True})
        else:
            return Response({'exists': False})


class ReportReasonList(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        reasons = []
        for reason in UserReportReason.objects.all():
            reasons.append(reason.reason)
        return Response({'reasons': reasons})


class TagAutocomplete(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        searcher = OurchiveSearch()
        results = searcher.do_tag_search(request.GET.get(
            'term'), request.GET.get('type'), request.GET.get('fetch_all', False))
        return Response({'results': results})


class WorkAutocomplete(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        searcher = OurchiveSearch()
        results = searcher.do_work_search(request.GET.get(
            'term'), request.user.id)
        return Response({'results': results})


class UserAutocomplete(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        searcher = OurchiveSearch()
        results = searcher.do_user_search(request.GET.get(
            'term'), request.user.id)
        return Response({'results': results})


class SeriesAutocomplete(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        searcher = OurchiveSearch()
        results = searcher.do_series_search(request.GET.get(
            'term'), request.user.id)
        return Response({'results': results})


class AnthologyAutocomplete(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        searcher = OurchiveSearch()
        results = searcher.do_anthology_search(request.GET.get(
            'term'), request.user.id)
        return Response({'results': results})


class FileUpload(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        if 'files[]' in request.FILES:
            if 'image' in request.FILES['files[]'].content_type:
                if not request.user.can_upload_images:
                    return Response({'message': _('User does not have permission to upload images.')}, status=403)
            elif 'audio' in request.FILES['files[]'].content_type:
                if not request.user.can_upload_audio:
                    return Response({'message': _('User does not have permission to upload audio.')}, status=403)
            elif 'video' in request.FILES['files[]'].content_type:
                if not request.user.can_upload_video:
                    return Response({'message': _('User does not have permission to upload video.')}, status=403)
            else:
                if not request.user.can_upload_export_files:
                    return Response({'message': 'User does not have permission to upload this file.'}, status=403)
            service = FileHelperService.get_service()
            if service is not None:
                final_url = service.handle_uploaded_file(
                    request.FILES['files[]'], request.FILES['files[]'].name, request.user.username)
                if final_url is None:
                    return Response({'message': 'Filetype not permitted.'}, status=403)
                return Response({'final_url': final_url})
            else:
                return Response({'final_url': 'This instance is trying to use a file processor not supported by file helpers. Please contact your administrator.'}, status=400)


class Invitations(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        email_decoded = request.GET.get('email').replace('%40', '@').replace('+', '%2B')
        invitation = Invitation.objects.filter(
            invite_token=request.GET.get('invite_token'), email=email_decoded).first()
        if invitation:
            if not invitation.token_used:
                return Response({'invitation': invitation.invite_token}, status=200)
            else:
                return Response({'message': _("Invitation has already been used. Please request a new invite link.")}, status=418)
        else:
            return Response({}, status=404)

    def post(self, request):
        existing_user = User.objects.filter(email=request.data['email']).first()
        if existing_user:
            return Response({'message': 'User is already registered.'}, status=418)
        invitation = Invitation()
        invitation.email = html.escape(request.data['email']).replace('+', '%2B')
        invitation.join_reason = nh3.clean(request.data['join_reason'])
        invitation.invite_token = get_random_string(length=100)
        invitation.register_link = f"{settings.ALLOWED_HOSTS[0]}/register?invite_token={invitation.invite_token}&email={invitation.email}"
        invitation.save()
        send_mail(
            _("New Registration Request"),
            _(f"You've received a new registration request for Ourchive. Go to 'Invitations' in your admin site to review."),
            settings.DEFAULT_FROM_EMAIL,
            [settings.SERVER_EMAIL],
            fail_silently=False,
        )
        return Response({}, status=200)


class PublishWork(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwnerOrReadOnly]

    def patch(self, request, pk):
        work_id = request.data['id']
        work = Work.objects.filter(id=work_id).first()
        work.draft = False
        for chapter in work.chapters.all():
            chapter.draft = False
            chapter.save()
        work.save()
        return Response({}, status=200)


class ExportWork(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwnerOrReadOnly]

    def get(self, request, pk):
        work = Work.objects.filter(id=pk).first()
        if work.draft and request.user.id != work.user.id:
            return Response({'message': ["You do not have permission to download this work."]}, status=400)
        work_url = ''
        # get export if it hasn't been created already.
        # note the archive has no M4B creation capability, so that's going to
        # be in preferred download url or nowhere.
        ext = request.GET.get('extension')
        if not ext:
            return Response({'message': ["GET param 'extension' must be supplied"]}, status=400)
        if ext.lower() == 'epub':
            if work.epub_url and work.epub_url != "None":
                media_url = work_export.get_epub_dir(work)
                return Response({'media_url': media_url}, status=200)
            work_url = work_export.create_epub(work)
            work.epub_url = work_url[1]
            # full_url = f'{settings.API_PROTOCOL}{settings.ALLOWED_HOSTS[0]}{work_url}'
            work.save()
            return Response({'media_url': work_url[0]}, status=200)
        elif ext.lower() == 'zip':
            if work.zip_url and work.zip_url != "None":
                return Response({'message': "ZIP url exists. Use ZIP URL to download work."}, status=400)
            work_url = work_export.create_zip(work)
            work.zip_url = work_url[1]
            work.save()
            return Response({'media_url': work_url[0]}, status=200)
        else:
            return Response({'message': ['Format not supported or work does not exist.']}, status=400)


class ImportWorks(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if 'work_id' not in request.data and 'username' not in request.data:
            return Response({'message': 'work_id or username required for import.'}, status=400)
        if 'save_as_draft' not in request.data or 'allow_anon_comments' not in request.data or 'allow_comments' not in request.data:
            return Response({'message': 'save_as_draft, allow_anon_comments, and allow_comments required for work import.'}, status=400)
        importer = ao3.work_import.EtlWorkImport(
            request.user.id,
            request.data['save_as_draft'],
            request.data['allow_anon_comments'],
            request.data['allow_comments'])
        if 'work_id' in request.data:
            id_or_url = request.data['work_id']
            parsed_id = util.parse_work_id_from_ao3_url(id_or_url)
            t = threading.Thread(target=importer.get_single_work,
                                 args=[parsed_id], daemon=True)
        elif 'username' in request.data:
            t = threading.Thread(target=importer.get_works_by_username, args=[
                                 request.data['username']], daemon=True)
        t.start()
        return Response({'message': "Import started"}, status=200)


class ImportStatus(generics.ListAPIView):
    serializer_class = ImportSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return WorkImport.objects.filter(job_finished=False, user__id=self.request.user.id).order_by('-created_on')


class ExportChives(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        if not 'export_works' in request.data and not 'export_bookmarks' in request.data and not 'export_collections' in request.data:
            return Response({'message': ["export_works, export_bookmarks, or export_collections required."]}, status=400)
        export_job = ChiveExport(
            user_id=request.user.id,
            export_works=request.data.get('export_works', "false").lower() == "true",
            export_bookmarks=request.data.get('export_bookmarks', "false").lower() == "true",
            export_collections=request.data.get('export_collections', "false").lower() == "true")
        export_job.save()
        return Response({'message': 'Export started.'}, status=200)

    def get(self, request, format=None):
        return Response({'export_works': 'false', 'export_bookmarks': 'false', 'export_collections': 'false'}, status=200)


# TODO: these classes are redundant, probably not best practice! Some approval operations aren't RESTful
# but this should be improved
class UserApprovalList(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        data = []
        pending_works = UserWork.objects.filter(user__id=request.user.id).filter(approved=False)
        pending_collections = UserCollection.objects.filter(user__id=request.user.id).filter(approved=False)
        pending_anthologies = UserAnthology.objects.filter(user__id=request.user.id).filter(approved=False)
        for work in pending_works:
            approval = {
                'id': f'{work.id}_work',
                'type': 'work',
                'creating_user': {'id': work.work.user.id, 'username': work.work.user.username},
                'chive': work.work.id,
                'title': work.work.title
            }
            data.append(approval)
        for collection in pending_collections:
            approval = {
                'id': f'{collection.id}_collection',
                'type': 'collection',
                'creating_user': {'id': collection.collection.user.id, 'username': collection.collection.user.username},
                'chive': collection.collection.id,
                'title': collection.collection.title
            }
            data.append(approval)
        for anthology in pending_anthologies:
            approval = {
                'id': f'{anthology.id}_anthology',
                'type': 'anthology',
                'creating_user': {'id': anthology.anthology.user.id, 'username': anthology.anthology.creating_user.username},
                'chive': anthology.anthology.id,
                'title': anthology.anthology.title
            }
            data.append(approval)
        return Response(data, status=200)


class UserApprovalRemove(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        user_to_remove = request.user.id
        type_to_remove = request.data.get('type', None)
        approval_id = request.data.get('id', None)
        approval = None
        if type_to_remove == 'work':
            approval = UserWork.objects.get(id=approval_id)
        elif type_to_remove == 'collection':
            approval = UserCollection.objects.get(id=approval_id)
        elif type_to_remove == 'anthology':
            approval = UserAnthology.objects.get(id=approval_id)
        else:
            return Response({'message': [_('type_to_remove must be in POST request and must be work, anthology or collection.')]}, status=400)
        if not approval:
            return Response({'message': [_(f'Approval having id {approval_id} does not exist.')]}, status=403)
        if approval.user.id != user_to_remove:
            return Response({'message': [_('Request user is not record user.')]}, status=403)
        approval.delete()
        return Response({'message': _('Association removed.')}, status=200)


class UserApprovalApprove(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        user_to_approve = request.user.id
        type_to_approve = request.data.get('type', None)
        approval_id = request.data.get('id', None)
        approval = None
        if type_to_approve == 'work':
            approval = UserWork.objects.get(id=approval_id)
        elif type_to_approve == 'collection':
            approval = UserCollection.objects.get(id=approval_id)
        elif type_to_approve == 'anthology':
            approval = UserAnthology.objects.get(id=approval_id)
        else:
            return Response({'message': [_('type_to_remove must be in POST request and must be work, anthology or collection.')]}, status=400)
        if not approval:
            return Response({'message': [_(f'Approval having id {approval_id} does not exist.')]}, status=403)
        if approval.user.id != user_to_approve:
            return Response({'message': [_('Request user is not record user.')]}, status=403)
        approval.approved = True
        approval.save()
        return Response({'message': _('Association approved.')}, status=200)


class CocreateApproveBulk(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        pending_works = UserWork.objects.filter(user__id=request.user.id).filter(approved=False)
        pending_collections = UserCollection.objects.filter(user__id=request.user.id).filter(approved=False)
        pending_anthologies = UserAnthology.objects.filter(user__id=request.user.id).filter(approved=False)
        for work in pending_works:
            work.approved = True
            work.save()
        for collection in pending_collections:
            collection.approved = True
            collection.save()
        for anthology in pending_anthologies:
            anthology.approved = True
            anthology.save()
        return Response({'message': _('Cocreators approved.')}, status=200)


class CocreateRejectBulk(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        pending_works = UserWork.objects.filter(user__id=request.user.id).filter(approved=False)
        pending_collections = UserCollection.objects.filter(user__id=request.user.id).filter(approved=False)
        pending_anthologies = UserAnthology.objects.filter(user__id=request.user.id).filter(approved=False)
        for work in pending_works:
            work.delete()
        for collection in pending_collections:
            collection.delete()
        for anthology in pending_anthologies:
            anthology.delete()
        return Response({'message': _('Cocreators rejected.')}, status=200)


class UserList(generics.ListCreateAPIView):
    queryset = User.objects.get_queryset().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [RegistrationPermitted]

    def perform_create(self, serializer):
        if 'invite_code' in self.request.data:
            serializer.save(
                invite_code=self.request.data['invite_code'], email=self.request.data['email'])
        else:
            serializer.save(
                email=self.request.data['email'] if 'email' in self.request.data else '')


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.get_queryset().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [RegistrationPermitted]

    def perform_create(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        serializer.save(attributes=attributes)

    def perform_update(self, serializer):
        if not self.request.user.can_upload_images and 'icon' in self.request.data:
            self.request.data.pop('icon')
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        serializer.save(attributes=attributes)

    def retrieve(self, request, *args, **kwargs):
        response = super(UserDetail, self).retrieve(request, args, kwargs)
        return response


class GroupList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ['groups']
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class UserWorkList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(user__username=self.kwargs['username']).filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('-updated_on')


class UserBookmarkList(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly, ObjectIsPrivate]

    def list(self, request, *args, **kwargs):
        response = super(UserBookmarkList, self).list(request, args, kwargs)
        try:
            if OurchiveSetting.objects.get(name='Rating Star Count') is not None:
                response.data['star_count'] = [x for x in range(
                    1, int(OurchiveSetting.objects.get(name='Rating Star Count').value) + 1)]
            else:
                response.data['star_count'] = [1, 2, 3, 4, 5]
        except ObjectDoesNotExist:
            response.data['star_count'] = [1, 2, 3, 4, 5]
        return response

    def get_queryset(self):
        if self.request.GET.get('draft', 'true').lower() == 'false':
            return Bookmark.objects.filter(user__username=self.kwargs['username']).filter(draft=False).order_by('-updated_on')
        return Bookmark.objects.filter(user__username=self.kwargs['username']).filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('-updated_on')


class UserBookmarkCollectionList(generics.ListCreateAPIView):
    serializer_class = BookmarkCollectionSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def get_queryset(self):
        queryset = BookmarkCollection.objects.filter(user__username=self.kwargs['username']).filter(Q(draft=False) | Q(user__id=self.request.user.id))
        if (self.request.GET.get('work_id', None)):
            queryset = queryset.exclude(works__id=self.request.GET.get('work_id'))
        return queryset.order_by('-updated_on')


class UserBookmarkDraftList(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Bookmark.objects.filter(draft=True, user__username=self.kwargs['username'])


class UserNameDetail(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return User.objects.filter(pk=self.kwargs['pk'])


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.get_queryset().order_by('id')
    serializer_class = GroupSerializer


class WorkList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('-updated_on')

    def perform_create(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if not self.request.user.can_upload_images and 'cover_url' in self.request.data:
            self.request.data.pop('cover_url')
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(user=self.request.user, attributes=attributes)


class UserWorkDraftList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(draft=True, user__username=self.kwargs['username']).order_by('-updated_on')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserBlocksList(generics.ListCreateAPIView):
    serializer_class = UserBlocksSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        if 'username' in self.kwargs and self.kwargs['username'] is not None:
            return UserBlocks.objects.filter(user__username=self.kwargs['username'])
        return UserBlocks.objects.all()


class UserBlocksDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserBlocksSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return UserBlocks.objects.filter(id=self.kwargs['pk'])


class UserBlockSingleDetail(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        blocked_user = UserBlocks.objects.filter(user__id=request.user.id, blocked_user__id=user_id).first()
        if blocked_user:
            return Response({'user_blocked': True, 'block_id': blocked_user.id}, status=200)
        else:
            return Response({'user_blocked': False}, status=200)


class UserReportList(generics.ListCreateAPIView):
    serializer_class = UserReportSerializer
    permission_classes = [IsOwner]
    queryset = UserReport.objects.all().order_by('created_on')


class UserReportDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserReportSerializer
    permission_classes = [IsOwner]
    queryset = UserReport.objects.all().order_by('created_on')


class SubscriptionList(generics.ListCreateAPIView):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        if 'subscribed_to' in self.request.GET and self.request.GET.get('subscribed_to') is not None:
            return UserSubscription.objects.filter(user__id=self.request.user.id, subscribed_user__username=self.request.GET.get('subscribed_to'))
        return UserSubscription.objects.all().order_by('-created_on')


class UserSubscriptionList(generics.ListCreateAPIView):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return UserSubscription.objects.filter(user__id=self.request.user.id)


class UserSubscriptionBookmarkList(generics.ListAPIView):
    serializer_class = BookmarkSummarySerializer
    permission_classes = [IsOwner, ObjectIsPrivate]

    def get_queryset(self):
        subscriptions = UserSubscription.objects.filter(
            user__id=self.request.user.id).filter(
            subscribed_to_bookmark=True)
        ids = subscriptions.values_list('subscribed_user', flat=True).all()
        return Bookmark.objects.filter(draft=False).filter(user__id__in=ids).order_by('-created_on')


class UserSubscriptionBookmarkCollectionList(generics.ListAPIView):
    serializer_class = BookmarkCollectionSummarySerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        subscriptions = UserSubscription.objects.filter(
            user__id=self.request.user.id).filter(
            subscribed_to_collection=True)
        ids = subscriptions.values_list('subscribed_user', flat=True).all()
        return BookmarkCollection.objects.filter(draft=False).filter(user__id__in=ids).order_by('-created_on')


class UserSubscriptionWorkList(generics.ListAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsOwner, ObjectIsPrivate]

    def get_queryset(self):
        subscriptions = UserSubscription.objects.filter(
            user__id=self.request.user.id).filter(
            subscribed_to_work=True)
        ids = subscriptions.values_list('subscribed_user', flat=True).all()
        return Work.objects.filter(draft=False).filter(user__id__in=ids).order_by('-created_on')


class UserSubscriptionSeriesList(generics.ListAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        subscriptions = UserSubscription.objects.filter(
            user__id=self.request.user.id).filter(
            subscribed_to_series=True)
        ids = subscriptions.values_list('subscribed_user', flat=True).all()
        return WorkSeries.objects.filter(user__id__in=ids).order_by('-created_on')


class UserSubscriptionAnthologyList(generics.ListAPIView):
    serializer_class = AnthologySerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        anthologies = UserSubscription.objects.filter(
            user__id=self.request.user.id).filter(
            subscribed_to_anthology=True)
        ids = anthologies.values_list('subscribed_user', flat=True).all()
        return Anthology.objects.filter(owners__id__in=ids).order_by('-created_on')


class UserSubscriptionDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return UserSubscription.objects.filter(user__id=self.request.user.id)


class WorkDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def retrieve(self, request, *args, **kwargs):
        response = super(WorkDetail, self).retrieve(request, args, kwargs)
        response.data['download_choices'] = Work.DOWNLOAD_CHOICES
        return response

    def perform_create(self, serializer):
        if not self.request.user.can_upload_images and 'cover_url' in self.request.data:
            self.request.data.pop('cover_url')
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(attributes=attributes)

    def perform_update(self, serializer):
        if not self.request.user.can_upload_images and 'cover_url' in self.request.data:
            self.request.data.pop('cover_url')
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(attributes=attributes)


class WorkDraftDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Work.objects.get_queryset().order_by('id')
    serializer_class = WorkSerializer
    permission_classes = [IsMultiOwner]


class FingergunDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Fingergun.objects.get_queryset().order_by('id')
    serializer_class = FingergunSerializer
    permission_classes = [IsOwnerOrReadOnly]


class FingergunList(generics.ListCreateAPIView):
    queryset = Fingergun.objects.get_queryset().order_by('id')
    serializer_class = FingergunSerializer
    permission_classes = [IsOwnerOrReadOnly]


class FingergunByWorkList(generics.ListCreateAPIView):
    serializer_class = FingergunSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Fingergun.objects.filter(work__id=self.kwargs['work_id'])


class WorkTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkType.objects.get_queryset().order_by('id')
    serializer_class = WorkTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class WorkTypeList(generics.ListCreateAPIView):
    queryset = WorkType.objects.get_queryset().order_by('sort_order')
    serializer_class = WorkTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class WorkByTypeList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(work_type__id=self.kwargs['type_id']).order_by('-updated_on')


class WorkByTagList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(tags__id=self.kwargs['pk']).order_by('-updated_on')


class TagTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = TagType.objects.get_queryset().order_by('id')
    serializer_class = TagTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class TagTypeList(generics.ListCreateAPIView):
    serializer_class = TagTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if 'admin_administrated' in self.request.GET and self.request.GET.get('admin_administrated') is not None:
            return TagType.objects.filter(admin_administrated=self.request.GET.get('admin_administrated'))
        return TagType.objects.all()


class BrowsableTagType(generics.ListCreateAPIView):
    serializer_class = TagTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return TagType.objects.filter(show_for_browse=True)


class TagsByType(generics.ListCreateAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Tag.objects.filter(tag_type_id=self.request.GET.get('tag_type'))


class TagList(generics.ListCreateAPIView):
    queryset = Tag.objects.get_queryset().order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(display_text=self.request.data['text'], user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(
            display_text=self.request.data['display_text'], user=self.request.user)


class TopTagList(generics.ListAPIView):
    serializer_class = TopTagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = NonPaginatedResultSetPagination

    def get_queryset(self):
        return Tag.objects.filter(tag_type__show_in_aggregate=True).annotate(num_uses=Count("bookmark") + Count("work")).order_by("-num_uses")[:15]


class RecentWorksList(generics.ListAPIView):
    serializer_class = WorkSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = NonPaginatedResultSetPagination

    def get_queryset(self):
        return Work.objects.filter(draft=False).order_by("-updated_on")[:10]


class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.get_queryset().order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(display_text=self.request.data['text'], user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(
            display_text=self.request.data['display_text'], user=self.request.user)


class ChapterList(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsWorkOwnerOrReadOnly]

    def get_queryset(self):
        return Chapter.objects.get_queryset().filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('number')

    def perform_create(self, serializer):
        if not self.request.user.can_upload_images and 'image_url' in self.request.data:
            self.request.data.pop('image_url')
        if not self.request.user.can_upload_audio and 'audio_url' in self.request.data:
            self.request.data.pop('audio_url')
        if not self.request.user.can_upload_video and 'video_url' in self.request.data:
            self.request.data.pop('video_url')
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(user=self.request.user)


class ChapterDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsWorkOwnerOrReadOnly]

    def get_queryset(self):
        return Chapter.objects.get_queryset().filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_create(self, serializer):
        if not self.request.user.can_upload_images and 'image_url' in self.request.data:
            self.request.data.pop('image_url')
        if not self.request.user.can_upload_audio and 'audio_url' in self.request.data:
            self.request.data.pop('audio_url')
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(attributes=attributes)

    def perform_update(self, serializer):
        if not self.request.user.can_upload_images and 'image_url' in self.request.data:
            self.request.data.pop('image_url')
        if not self.request.user.can_upload_images and 'audio_url' in self.request.data:
            self.request.data.pop('audio_url')
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(attributes=attributes)


class WorkChapterDetail(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsWorkOwnerOrReadOnly]

    def get_queryset(self):
        return Chapter.objects.filter(work__id=self.kwargs['work_id']).filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('number')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChapterDraftList(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsWorkOwner]

    def get_queryset(self):
        return Chapter.objects.get_queryset().order_by('number')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChapterDraftDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Chapter.objects.get_queryset().order_by('id')
    serializer_class = ChapterSerializer
    permission_classes = [IsWorkOwner]


class WorkChapterDetailAll(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsWorkOwner]
    pagination_class = None

    def get_queryset(self):
        return Chapter.objects.filter(work__id=self.kwargs['work_id']).order_by('number')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkCommentList(generics.ListCreateAPIView):
    serializer_class = ChapterCommentSerializer
    permission_classes = [IsMultiOwnerOrReadOnly,
                          UserAllowsWorkComments, UserAllowsWorkAnonComments]

    def get_queryset(self):
        return ChapterComment.objects.filter(chapter__work__id=self.kwargs['pk']).filter(parent_comment=None).order_by('created_on')


class ChapterCommentDetail(generics.ListCreateAPIView):
    serializer_class = ChapterCommentSerializer
    permission_classes = [IsWorkOwnerOrReadOnly,
                          UserAllowsWorkComments, UserAllowsWorkAnonComments]

    def get_queryset(self):
        return ChapterComment.objects.filter(chapter__id=self.kwargs['pk']).filter(parent_comment=None).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkList(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly, WorkIsNotDraft, ObjectIsPrivate]

    def list(self, request, *args, **kwargs):
        response = super(BookmarkList, self).list(request, args, kwargs)
        try:
            if OurchiveSetting.objects.get(name='Rating Star Count') is not None:
                response.data['star_count'] = [x for x in range(
                    1, int(OurchiveSetting.objects.get(name='Rating Star Count').value) + 1)]
            else:
                response.data['star_count'] = [1, 2, 3, 4, 5]
        except ObjectDoesNotExist:
            response.data['star_count'] = [1, 2, 3, 4, 5]
        return response

    def create(self, request, *args, **kwargs):
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        response = super(BookmarkList, self).create(request, args, kwargs)
        response.data['star_count'] = get_star_count(
            OurchiveSetting.objects.get(name='Rating Star Count'))
        return response

    def get_queryset(self):
        if self.request.GET.get('draft', 'true').lower() == 'false':
            return Bookmark.objects.filter(draft=False).order_by('-updated_on')
        else:
            return Bookmark.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id)).filter(Q(is_private=False) | Q(user__id=self.request.user.id)).order_by('-updated_on')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkByTagList(generics.ListAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsAdminOrReadOnly, ObjectIsPrivate]

    def get_queryset(self):
        return Bookmark.objects.filter(tags__id=self.kwargs['pk']).filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('-updated_on')


class BookmarkDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly, WorkIsNotDraft, ObjectIsPrivate]

    def retrieve(self, request, *args, **kwargs):
        response = super(BookmarkDetail, self).retrieve(request, args, kwargs)
        response.data['star_count'] = get_star_count(
            OurchiveSetting.objects.get(name='Rating Star Count'))
        return response

    def get_queryset(self):
        return Bookmark.objects.get_queryset().filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_create(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(attributes=attributes)

    def perform_update(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(attributes=attributes)


class BookmarkDraftDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return Bookmark.objects.filter(draft=True).order_by('id')


class BookmarkCommentDetail(generics.ListCreateAPIView):
    serializer_class = BookmarkCommentSerializer
    permission_classes = [UserAllowsBookmarkComments, UserAllowsBookmarkAnonComments]

    def get_queryset(self):
        return BookmarkComment.objects.filter(bookmark__id=self.kwargs['pk']).filter(parent_comment=None).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkPrimaryCommentDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookmarkCommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return BookmarkComment.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.bookmark.comment_count = instance.bookmark.comment_count - 1
        instance.bookmark.save()
        if instance.parent_comment is not None:
            instance.user = None
            instance.text = "This comment has been deleted."
            instance.save()
        else:
            instance.delete()


class BookmarkCollectionList(generics.ListCreateAPIView):
    serializer_class = BookmarkCollectionSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def get_queryset(self):
        return BookmarkCollection.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('-updated_on')

    def perform_create(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if not self.request.user.can_upload_images and 'header_url' in self.request.data:
            self.request.data.pop('header_url')
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(user=self.request.user, attributes=attributes)


class BookmarkCollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookmarkCollectionSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def get_queryset(self):
        return BookmarkCollection.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_update(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if not self.request.user.can_upload_images and 'header_url' in self.request.data:
            self.request.data.pop('header_url')
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(user=self.request.user, attributes=attributes)

    def perform_create(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if not self.request.user.can_upload_images and 'header_url' in self.request.data:
            self.request.data.pop('header_url')
        serializer.save(user=self.request.user, attributes=attributes)


class BookmarkCollectionWork(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        target_collection = request.data.get('collection_id', None)
        work_id = request.data.get('work_id', None)
        if not target_collection or not work_id:
            return Response({'message': [_('Missing field: collection_id and work_id required for POST request.')]}, status=400)
        collection = BookmarkCollection.objects.get(id=target_collection)
        work_to_add = Work.objects.get(id=work_id)
        if not collection or not work_to_add:
            return Response({'message': [_('Collection or work not found.')]}, status=404)
        if not collection.user.id == request.user.id:
            return Response({'message': [_('You do not have permission to modify this collection')]}, status=403)
        collection.works.add(work_to_add)
        collection.save()
        return Response({'message': ['Work added to collection.']})


class CommentList(generics.ListCreateAPIView):
    serializer_class = ChapterCommentSerializer
    permission_classes = [UserAllowsWorkComments, UserAllowsWorkAnonComments]

    def get_queryset(self):
        return ChapterComment.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        offset = self.request.data.get('offset', 0)
        serializer.save(user=self.request.user, offset=offset, comment_thread=self.request.data.get('comment_thread', None), comment_count=self.request.data.get('comment_count', None))


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChapterComment.objects.get_queryset().order_by('id')
    serializer_class = ChapterCommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_destroy(self, instance):
        instance.chapter.work.comment_count = instance.chapter.work.comment_count - 1
        instance.chapter.comment_count = instance.chapter.comment_count - 1
        instance.chapter.work.save()
        instance.chapter.save()
        if instance.parent_comment is not None:
            instance.user = None
            instance.text = "This comment has been deleted."
            instance.save()
        else:
            instance.delete()


class BookmarkCommentList(generics.ListCreateAPIView):
    serializer_class = BookmarkCommentSerializer
    permission_classes = [UserAllowsBookmarkComments, UserAllowsBookmarkAnonComments]

    def get_queryset(self):
        return BookmarkComment.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CollectionCommentList(generics.ListCreateAPIView):
    serializer_class = CollectionCommentSerializer
    permission_classes = [UserAllowsCollectionComments,
                          UserAllowsCollectionAnonComments]

    def get_queryset(self):
        return CollectionComment.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CollectionCommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CollectionComment.objects.get_queryset().order_by('id')
    serializer_class = CollectionCommentSerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def perform_destroy(self, instance):
        instance.collection.comment_count = instance.collection.comment_count - 1
        instance.collection.comment_count = instance.collection.comment_count - 1
        instance.collection.save()
        if instance.parent_comment is not None:
            instance.user = None
            instance.text = "This comment has been deleted."
            instance.save()
        else:
            instance.delete()


class BookmarkCollectionCommentDetail(generics.ListCreateAPIView):
    serializer_class = CollectionCommentSerializer
    permission_classes = [UserAllowsCollectionComments,
                          UserAllowsCollectionAnonComments]

    def get_queryset(self):
        return CollectionComment.objects.filter(collection__id=self.kwargs['pk']).filter(parent_comment=None).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MessageList(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Message.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MessageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Message.objects.get_queryset().order_by('id')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAdminUser]


class NotificationTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = NotificationType.objects.get_queryset().order_by('id')
    serializer_class = NotificationTypeSerializer
    permission_classes = [permissions.IsAdminUser]


class NotificationTypeList(generics.ListCreateAPIView):
    queryset = NotificationType.objects.get_queryset().order_by('id')
    serializer_class = NotificationTypeSerializer
    permission_classes = [permissions.IsAdminUser]


class NotificationList(generics.ListCreateAPIView):
    queryset = Notification.objects.get_queryset().order_by('id')
    serializer_class = NotificationSerializer
    permission_classes = [IsOwner]


class NotificationRead(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwner]

    def patch(self, request, format=None):
        notifications = Notification.objects.filter(
            user__id=request.user.id, read=False).all()
        for notification in notifications:
            notification.read = True
            notification.save()
        user = User.objects.get(id=request.user.id)
        user.has_notifications = False
        user.save()
        return Response({'results': 'Notifications marked as read.'})


class NotificationDelete(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwner]

    def patch(self, request, format=None):
        notifications = Notification.objects.filter(
            user__id=request.user.id).all()
        for notification in notifications:
            notification.delete()
        user = User.objects.get(id=request.user.id)
        user.has_notifications = False
        user.save()
        return Response({'results': 'Notifications marked as read.'})


class UserNotificationList(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return Notification.objects.filter(user__id=self.request.user.id).order_by('read', '-created_on')


class NotificationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.get_queryset().order_by('id')
    serializer_class = NotificationSerializer
    permission_classes = [IsOwner]


class OurchiveSettingList(generics.ListCreateAPIView):
    serializer_class = OurchiveSettingSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = NonPaginatedResultSetPagination

    def get_queryset(self):
        if 'setting_name' in self.request.GET:
            return OurchiveSetting.objects.filter(name=self.request.GET['setting_name'])
        else:
            return OurchiveSetting.objects.order_by('id')


class OurchiveSettingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = OurchiveSetting.objects.get_queryset().order_by('id')
    serializer_class = OurchiveSettingSerializer
    permission_classes = [IsAdminOrReadOnly]


class AttributeTypeList(generics.ListCreateAPIView):
    serializer_class = AttributeTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = AttributeType.objects
        if 'allow_on_work' in self.request.GET:
            queryset = queryset.filter(allow_on_work=self.request.GET['allow_on_work'])
        elif 'allow_on_bookmark' in self.request.GET:
            queryset = queryset.filter(
                allow_on_bookmark=self.request.GET['allow_on_bookmark'])
        elif 'allow_on_chapter' in self.request.GET:
            queryset = queryset.filter(
                allow_on_chapter=self.request.GET['allow_on_chapter'])
        elif 'allow_on_user' in self.request.GET:
            queryset = queryset.filter(allow_on_user=self.request.GET['allow_on_user'])
        elif 'allow_on_bookmark_collection' in self.request.GET:
            queryset = queryset.filter(
                allow_on_bookmark_collection=self.request.GET['allow_on_bookmark_collection'])
        elif self.request.GET.get('allow_on_anthology', None):
            queryset = queryset.filter(
                allow_on_anthology=self.request.GET.get('allow_on_anthology'))
        else:
            return AttributeType.objects.order_by('name')
        return queryset.order_by('name')


class BrowsableAttributeType(generics.ListCreateAPIView):
    serializer_class = AttributeTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return AttributeType.objects.filter(show_for_browse=True)


class AttributesByType(generics.ListCreateAPIView):
    serializer_class = AttributeValueSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return AttributeValue.objects.filter(attribute_type_id=self.request.GET.get('attribute_type'))


class AttributeTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = AttributeType.objects.get_queryset().order_by('name')
    serializer_class = AttributeTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class AttributeValueList(generics.ListCreateAPIView):
    queryset = AttributeValue.objects.get_queryset().order_by('name')
    serializer_class = AttributeValueSerializer
    permission_classes = [IsAdminOrReadOnly]


class AttributeValueDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = AttributeValue.objects.get_queryset().order_by('name')
    serializer_class = AttributeValueSerializer
    permission_classes = [IsAdminOrReadOnly]


class ContentPageList(generics.ListCreateAPIView):
    serializer_class = ContentPageSerializer
    permission_classes = [ObjectIsLocked]

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            return ContentPage.objects.filter(locked_to_users=False)
        else:
            return ContentPage.objects.all()


class ContentPageMandatoryList(generics.ListAPIView):
    serializer_class = ContentPageSerializer
    permission_classes = [ObjectIsLocked]
    pagination_class = NonPaginatedResultSetPagination

    def get_queryset(self):
        return ContentPage.objects.filter(locked_to_users=False, agree_on_signup=True).order_by('id')


class ContentPageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ContentPage.objects.get_queryset()
    serializer_class = ContentPageDetailSerializer
    permission_classes = [ObjectIsLocked]


class AdminAnnouncementList(generics.ListCreateAPIView):
    serializer_class = AdminAnnouncementSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = AdminAnnouncement.objects.get_queryset()


class AdminAnnouncementActiveList(generics.ListAPIView):
    serializer_class = AdminAnnouncementSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = NonPaginatedResultSetPagination

    def get_queryset(self):
        return AdminAnnouncement.objects.exclude(expires_on__lte=datetime.datetime.now()).filter(active=True).order_by('id')


class AdminAnnouncementDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = AdminAnnouncement.objects.get_queryset()
    serializer_class = AdminAnnouncementSerializer
    permission_classes = [permissions.IsAdminUser]


class LanguageList(generics.ListAPIView):
    queryset = Language.objects.get_queryset()
    serializer_class = LanguageSerializer
    permission_classes = [IsAdminOrReadOnly]


class NewsList(generics.ListAPIView):
    queryset = News.objects.get_queryset()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]


class NewsDetail(generics.RetrieveAPIView):
    queryset = News.objects.get_queryset()
    serializer_class = NewsSerializer
    permission_classes = [IsAdminOrReadOnly]


class SeriesList(generics.ListCreateAPIView):
    queryset = WorkSeries.objects.get_queryset()
    serializer_class = SeriesSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(user=self.request.user)


class SeriesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkSeries.objects.get_queryset()
    serializer_class = SeriesSerializer
    permission_classes = [IsWorksMultiOwnerOrReadOnly]

    def perform_update(self, serializer):
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(user=self.request.user)


class WorkSeriesList(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwnerOrReadOnly]

    def patch(self, request, pk):
        works = request.data
        tracking = 1
        for work_obj in works:
            work = Work.objects.get(id=work_obj['work'])
            work.series_num = int(work_obj['series_num']) if str(work_obj['series_num']).isdigit() else tracking
            work.save()
            tracking = tracking + 1
        return Response({'message': 'Work series numbers updated.'}, status=200)


class WorkSeriesDetail(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwnerOrReadOnly]

    def delete(self, request, pk, work_id):
        work = Work.objects.get(id=work_id)
        work.series = None
        work.series_num = None
        work.save()
        return Response({'message': 'Work removed from series.'}, status=200)


class UserSeriesList(generics.ListCreateAPIView):
    serializer_class = SeriesSerializer
    permission_classes = [IsWorksMultiOwnerOrReadOnly]

    def get_queryset(self):
        return WorkSeries.objects.filter(works__work_users__user__username=self.kwargs['username']).order_by('-updated_on')


class UserAnthologyList(generics.ListCreateAPIView):
    serializer_class = AnthologySerializer
    permission_classes = [IsWorksMultiOwnerOrReadOnly]

    def get_queryset(self):
        return Anthology.objects.filter(Q(owners__username=self.kwargs['username']) | Q(creating_user__username=self.kwargs['username'])).order_by('-updated_on')


class AnthologyList(generics.ListCreateAPIView):
    queryset = Anthology.objects.get_queryset()
    serializer_class = AnthologySerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(creating_user=self.request.user, attributes=attributes)


class AnthologyDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Anthology.objects.get_queryset()
    serializer_class = AnthologySerializer
    permission_classes = [IsMultiOwnerOrReadOnly]

    def perform_update(self, serializer):
        attributes = []
        if 'attributes' in self.request.data:
            attributes = self.request.data['attributes']
        if 'created_on' in self.request.data and not self.request.data['created_on']:
            self.request.data['created_on'] = str(datetime.datetime.now().date())
        if 'updated_on' in self.request.data and not self.request.data['updated_on']:
            self.request.data['updated_on'] = str(datetime.datetime.now().date())
        serializer.save(creating_user=self.request.user, attributes=attributes)


class WorkAnthologyList(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwnerOrReadOnly]

    def patch(self, request, pk):
        works = request.data
        tracking = 1
        for work_obj in works:
            anthology_work = AnthologyWork.objects.get(work__id=work_obj['work'], anthology__id=work_obj['anthology'])
            anthology_work.sort_order = int(work_obj['sort_order']) if str(work_obj['sort_order']).isdigit() else tracking
            anthology_work.save()
            tracking = tracking + 1
        return Response({'message': 'Work anthology order updated.'}, status=200)


class WorkAnthologyDetail(APIView):
    parser_classes = [JSONParser]
    permission_classes = [IsOwnerOrReadOnly]

    def delete(self, request, pk, work_id):
        AnthologyWork.objects.delete(work__id=work_id, anthology__id=pk)
        return Response({'message': 'Work removed from anthology.'}, status=200)

