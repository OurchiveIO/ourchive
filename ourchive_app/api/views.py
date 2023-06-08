from django.shortcuts import render
from django.contrib.auth.models import Group
from rest_framework import viewsets, generics
from api.serializers import AttributeTypeSerializer, AttributeValueSerializer, UserSerializer, GroupSerializer, WorkSerializer, TagSerializer, BookmarkCollectionSerializer, ChapterSerializer, TagTypeSerializer, WorkTypeSerializer, BookmarkSerializer, ChapterCommentSerializer, BookmarkCommentSerializer, MessageSerializer, NotificationSerializer, NotificationTypeSerializer, OurchiveSettingSerializer, SearchResultsSerializer, FingergunSerializer, UserBlocksSerializer
from api.models import User, Work, Tag, Chapter, TagType, WorkType, Bookmark, BookmarkCollection, ChapterComment, BookmarkComment, Message, Notification, NotificationType, OurchiveSetting, Fingergun, UserBlocks, Invitation, AttributeType, AttributeValue
from rest_framework import generics, permissions
from api.permissions import IsOwnerOrReadOnly, UserAllowsBookmarkComments, UserAllowsBookmarkAnonComments, UserAllowsWorkComments, UserAllowsWorkAnonComments, IsOwner, IsAdminOrReadOnly, IsUser, RegistrationPermitted
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser
from .search.search_service import OurchiveSearch
from .search.search_obj import GlobalSearch
from django.db.models import Q
import json
import datetime
from django.utils.crypto import get_random_string
from django.conf import settings
import html
from .file_helpers import FileHelperService


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


class TagAutocomplete(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        searcher = OurchiveSearch()
        results = searcher.do_tag_search(request.GET.get('term'), request.GET.get('type'), request.GET.get('fetch_all', False))
        return Response({'results': results})


class FileUpload(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        if 'files[]' in request.FILES:
            service = FileHelperService.get_service()
            if service is not None:
                final_url = service.handle_uploaded_file(request.FILES['files[]'], request.FILES['files[]'].name, request.user.username)
                return Response({'final_url': final_url})
            else:
                return Response({'results': 'This instance is trying to use a file processor not supported by file helpers. Please contact your administrator.'}, status=400)


class Invitations(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        email_decoded = request.GET.get('email').replace('%40', '@').replace('+', '%2B')
        invitation = Invitation.objects.filter(invite_token=request.GET.get('invite_token'), email=email_decoded).first()
        if invitation:
            return Response({'invitation': invitation.invite_token}, status=200)
        else:
            return Response({}, status=404)

    def post(self, request):
        existing_user = User.objects.filter(email=request.data['email']).first()
        if existing_user:
            return Response({'message': 'User is already registered.'}, status=418)
        invitation = Invitation()
        invitation.email = html.escape(request.data['email']).replace('+', '%2B')
        invitation.invite_token = get_random_string(length=100)
        invitation.token_expiration = datetime.datetime.now() + datetime.timedelta(days=7)
        invitation.register_link = f"{settings.ALLOWED_HOSTS[0]}/register?invite_token={invitation.invite_token}&email={invitation.email}"
        invitation.save()
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


class UserList(generics.ListCreateAPIView):
    queryset = User.objects.get_queryset().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [RegistrationPermitted]

    def perform_create(self, serializer):
        serializer.save(invite_code=self.request.data['invite_code'], email=self.request.data['email'])


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.get_queryset().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [RegistrationPermitted]


class UserWorkList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(user__username=self.kwargs['username']).filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')


class UserBookmarkList(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Bookmark.objects.filter(user__username=self.kwargs['username']).order_by('id')


class UserBookmarkDraftList(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Bookmark.objects.filter(draft=True, user__username=self.kwargs['username'])


class UserNameDetail(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        username = self.kwargs['username']
        return User.objects.filter(username=username)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.get_queryset().order_by('id')
    serializer_class = GroupSerializer


class WorkList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserWorkDraftList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(draft=True, user__username=self.kwargs['username'])

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


class WorkDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_create(self, serializer):
        if 'attributes' in self.request.data:
            serializer.save(attributes=self.request.data['attributes'])

    def perform_update(self, serializer):
        if 'attributes' in self.request.data:
            serializer.save(attributes=self.request.data['attributes'])


class WorkDraftDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Work.objects.get_queryset().order_by('id')
    serializer_class = WorkSerializer
    permission_classes = [IsOwner]


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
    queryset = WorkType.objects.get_queryset().order_by('id')
    serializer_class = WorkTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class WorkByTypeList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(work_type__id=self.kwargs['type_id']).order_by('id')


class WorkByTagList(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Work.objects.filter(tags__id=self.kwargs['pk']).order_by('id')


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


class TagList(generics.ListCreateAPIView):
    queryset = Tag.objects.get_queryset().order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(display_text=self.request.data['text'], user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(display_text=self.request.data['display_text'], user=self.request.user)


class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.get_queryset().order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(display_text=self.request.data['text'], user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(display_text=self.request.data['display_text'], user=self.request.user)


class ChapterList(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Chapter.objects.get_queryset().filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChapterDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Chapter.objects.get_queryset().filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_create(self, serializer):
        if 'attributes' in self.request.data:
            serializer.save(attributes=self.request.data['attributes'])

    def perform_update(self, serializer):
        if 'attributes' in self.request.data:
            serializer.save(attributes=self.request.data['attributes'])


class WorkChapterDetail(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Chapter.objects.filter(work__id=self.kwargs['work_id']).filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('number')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChapterDraftList(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return Chapter.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChapterDraftDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Chapter.objects.get_queryset().order_by('id')
    serializer_class = ChapterSerializer
    permission_classes = [IsOwner]


class WorkDraftChapterDetail(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return Chapter.objects.filter(work__id=self.kwargs['work_id']).order_by('number')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChapterCommentDetail(generics.ListCreateAPIView):
    serializer_class = ChapterCommentSerializer
    permission_classes = [IsOwnerOrReadOnly, UserAllowsWorkComments, UserAllowsWorkAnonComments]

    def get_queryset(self):
        return ChapterComment.objects.filter(chapter__id=self.kwargs['pk']).filter(parent_comment=None).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkList(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Bookmark.objects.filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkByTagList(generics.ListCreateAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return Bookmark.objects.filter(tags__id=self.kwargs['pk']).filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')


class BookmarkDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return Bookmark.objects.get_queryset().filter(Q(draft=False) | Q(user__id=self.request.user.id)).order_by('id')

    def perform_create(self, serializer):
        if 'attributes' in self.request.data:
            serializer.save(attributes=self.request.data['attributes'])

    def perform_update(self, serializer):
        if 'attributes' in self.request.data:
            serializer.save(attributes=self.request.data['attributes'])


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
        instance.user = None
        instance.text = "This comment has been deleted"
        instance.save()


class BookmarkCollectionList(generics.ListCreateAPIView):
    serializer_class = BookmarkCollectionSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        return BookmarkCollection.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkCollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = BookmarkCollection.objects.get_queryset().order_by('id')
    serializer_class = BookmarkCollectionSerializer
    permission_classes = [IsOwnerOrReadOnly]


class CommentList(generics.ListCreateAPIView):
    serializer_class = ChapterCommentSerializer
    permission_classes = [UserAllowsWorkComments, UserAllowsWorkAnonComments]

    def get_queryset(self):
        return ChapterComment.objects.get_queryset().order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChapterComment.objects.get_queryset().order_by('id')
    serializer_class = ChapterCommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_destroy(self, instance):
        instance.chapter.work.comment_count = instance.chapter.work.comment_count - 1
        instance.chapter.comment_count = instance.chapter.comment_count - 1
        instance.chapter.work.save()
        instance.chapter.save()
        instance.user = None
        instance.text = "This comment has been deleted"
        instance.save()


class BookmarkCommentList(generics.ListCreateAPIView):
    serializer_class = BookmarkCommentSerializer
    permission_classes = [UserAllowsBookmarkComments, UserAllowsBookmarkAnonComments]

    def get_queryset(self):
        return BookmarkComment.objects.get_queryset().order_by('id')

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
    permission_classes = [IsOwner, permissions.IsAdminUser]


class UserNotificationList(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsOwner, permissions.IsAdminUser]

    def get_queryset(self):
        return Notification.objects.filter(user__id=self.request.user.id)


class NotificationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.get_queryset().order_by('id')
    serializer_class = NotificationSerializer
    permission_classes = [IsOwner, permissions.IsAdminUser]


class OurchiveSettingList(generics.ListCreateAPIView):
    serializer_class = OurchiveSettingSerializer
    permission_classes = [IsAdminOrReadOnly]

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
            queryset = queryset.filter(allow_on_bookmark=self.request.GET['allow_on_bookmark'])
        elif 'allow_on_chapter' in self.request.GET:
            queryset = queryset.filter(allow_on_chapter=self.request.GET['allow_on_chapter'])
        elif 'allow_on_user' in self.request.GET:
            queryset = queryset.filter(allow_on_user=self.request.GET['allow_on_user'])
        else:
            return AttributeType.objects.order_by('name')
        return queryset.order_by('name')


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
