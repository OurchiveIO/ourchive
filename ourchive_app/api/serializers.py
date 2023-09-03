from django.contrib.auth.models import Group, AnonymousUser
from rest_framework import serializers
from django.db import IntegrityError
from rest_framework_recursive.fields import RecursiveField
from .custom_fields import UserPrivateField
from api.models import Work, Tag, Chapter, TagType, WorkType, \
    Bookmark, BookmarkCollection, ChapterComment, BookmarkComment, Message, \
    NotificationType, Notification, OurchiveSetting, Fingergun, UserBlocks, \
    Invitation, AttributeType, AttributeValue, User, ContentPage, UserReport, \
    UserReportReason, UserSubscription, CollectionComment, AdminAnnouncement
import datetime
import logging
from django.conf import settings
from django.core.mail import send_mail
from .utils import convert_boolean, clean_text
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import unidecode
from etl.models import WorkImport

logger = logging.getLogger(__name__)


class AttributeValueSerializer(serializers.HyperlinkedModelSerializer):
    attribute_type = serializers.SlugRelatedField(
        queryset=AttributeType.objects.all(), slug_field='display_name')
    id = serializers.ReadOnlyField()

    def process_attributes(attr_obj, validated_data, attributes):
        attrs_to_add = []
        attr_types = set()
        for attribute in attributes:
            attribute = AttributeValue.objects.filter(name=attribute['name'], attribute_type__name=attribute['attribute_type']).first()
            if attribute is not None:
                if attribute.attribute_type.name in attr_types and attribute.attribute_type.allow_multiselect is False:
                    logger.error(f"Cannot add attribute value {attribute.name}; attribute type {attribute.attribute_type.name} does not allow multi-select.")
                else:
                    attrs_to_add.append(attribute)
                    attr_types.add(attribute.attribute_type.name)
        attr_obj.attributes.clear()
        for attr in attrs_to_add:
            attr_obj.attributes.add(attr)
        attr_obj.save()
        return attr_obj

    class Meta:
        model = AttributeValue
        fields = '__all__'


class AttributeTypeSerializer(serializers.HyperlinkedModelSerializer):
    attribute_values = AttributeValueSerializer(many=True, required=False)

    class Meta:
        model = AttributeType
        fields = '__all__'


class ContentPageSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    class Meta:
        model = ContentPage
        fields = '__all__'


class ContentPageDetailSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    value = serializers.ReadOnlyField()

    class Meta:
        model = ContentPage
        fields = '__all__'


class UserBlocksSerializer(serializers.HyperlinkedModelSerializer):
    uid = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    blocked_user_name = serializers.CharField(
        source='blocked_user.username',
        read_only=True
    )
    blocked_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)

    class Meta:
        model = UserBlocks
        fields = '__all__'


class UserReportSerializer(serializers.HyperlinkedModelSerializer):
    uid = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    reported_user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    reason = serializers.SlugRelatedField(queryset=UserReportReason.objects.all(),
        slug_field='reason')

    def create(self, validated_data):
        report = UserReport.objects.create(**validated_data)
        to_emails = []
        for user in User.objects.filter(is_superuser=True):
            to_emails.append(user.email)
        send_mail(
            f"New Reported User",
            f"{validated_data['user']} has reported {validated_data['reported_user']} for {validated_data['reason']}. Log in to the admin console to review.",
            settings.DEFAULT_FROM_EMAIL,
            to_emails,
            fail_silently=False,
        )
        return report

    class Meta:
        model = UserReport
        fields = '__all__'


class UserSubscriptionSerializer(serializers.HyperlinkedModelSerializer):
    uid = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    subscribed_user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    subscribed_user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    def update(self, subscription, validated_data):
        UserSubscription.objects.filter(id=subscription.id).update(**validated_data)
        subscription = UserSubscription.objects.get(id=subscription.id)
        if not subscription.subscribed_to_bookmark and not subscription.subscribed_to_collection:
            subscription.delete()
        return subscription

    class Meta:
        model = UserSubscription
        fields = '__all__'


class ImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkImport
        fields = '__all__'


class UserSerializer(serializers.HyperlinkedModelSerializer):
    work_set = serializers.HyperlinkedRelatedField(
        many=True, view_name='work-detail', read_only=True)
    bookmark_set = serializers.HyperlinkedRelatedField(
        many=True, view_name='bookmark-detail', read_only=True)
    userblocks_set = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="userblocks-detail")
    email = UserPrivateField()
    id = serializers.ReadOnlyField()
    can_upload_audio = serializers.ReadOnlyField(required=False)
    can_upload_images = serializers.ReadOnlyField(required=False)
    can_upload_export_files = serializers.ReadOnlyField(required=False)
    attributes = AttributeValueSerializer(many=True, required=False, read_only=True)
    default_work_type = serializers.SlugRelatedField(
        queryset=WorkType.objects.all(),
        slug_field='type_name', required=False)

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'password', 'email', 'groups',
                  'work_set', 'bookmark_set', 'userblocks_set', 'profile',
                  'icon', 'icon_alt_text', 'has_notifications', 'default_content',
                  'attributes', 'cookies_accepted', 'can_upload_audio', 'can_upload_export_files',
                  'can_upload_images', 'default_work_type', 'collapse_chapter_image',
                  'collapse_chapter_audio', 'collapse_chapter_text')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        require_invite = OurchiveSetting.objects.filter(
            name='Invite Only').first()
        if convert_boolean(require_invite.value):
            if 'invite_code' not in validated_data:
                raise serializers.ValidationError({"message": ["Invite only instance; invite_code must be present."]})
            invitation = Invitation.objects.filter(
                invite_token=validated_data['invite_code']).first()
            if invitation.token_expiration.date() >= datetime.datetime.now().date():
                invitation.token_used = True
                invitation.save()
            else:
                raise serializers.ValidationError({"message": ["Invite token has expired."]})
        if 'icon' not in validated_data:
            icon_alt_text = "Default icon"
            icon = OurchiveSetting.objects.filter(name='Default Icon URL').first()
            if icon is not None:
                icon = f"{settings.API_PROTOCOL}{settings.ALLOWED_HOSTS[0]}{settings.STATIC_URL}{icon.value}"
            else:
                icon = ''
        else:
            icon_alt_text = validated_data['icon_alt_text'] if 'icon_alt_text' in validated_data else ''
            icon = validated_data['icon']
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
        else:
            attributes = None
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            icon=icon,
            icon_alt_text=icon_alt_text
        )
        try:
            validate_password(validated_data['password'], user)
        except ValidationError:
            user.delete()
            raise serializers.ValidationError({"password": ["Password not valid. Password must be at least 10 character, not a common password, not similar to user's information, and not all numbers."]}, 400)
        user.set_password(validated_data['password'])
        user.save()
        if attributes is not None:
            user = AttributeValueSerializer.process_attributes(user, validated_data, attributes)
        return user

    def update(self, user, validated_data):
        if not validated_data['icon'] or validated_data['icon'].lower() == 'none':
            validated_data['icon_alt_text'] = "Default icon"
            icon = OurchiveSetting.objects.filter(name='Default Icon URL').first()
            if icon is not None:
                validated_data['icon'] = f"{settings.API_PROTOCOL}{settings.ALLOWED_HOSTS[0]}{settings.STATIC_URL}{icon.value}"
            else:
                validated_data['icon'] = ''
        validated_data['password'] = User.objects.filter(
            id=user.id).first().password
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
            user = AttributeValueSerializer.process_attributes(user, validated_data, attributes)
        User.objects.filter(id=user.id).update(**validated_data)
        return user


class SearchResultsSerializer(serializers.Serializer):
    work = serializers.DictField()
    bookmark = serializers.DictField()
    tag = serializers.DictField()
    user = serializers.DictField()


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class TagTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TagType
        fields = '__all__'


class WorkTypeSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = WorkType
        fields = '__all__'


class FingergunSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    work = serializers.PrimaryKeyRelatedField(
        queryset=Work.objects.all(), required=False)
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username', required=False, allow_null=True)

    class Meta:
        model = Fingergun
        fields = '__all__'

    def create(self, validated_data):
        '''
        Commented out "error handling" for now. TBH, I'm not sure
        we want to limit this to one-per-user.
        if (Fingergun.objects.filter(work__id=validated_data['work'].id) \
         .filter(user__id=validated_data['user'].id).all() is not None):
             return None'''
        fingergun = Fingergun.objects.create(**validated_data)
        work = Work.objects.filter(id=validated_data['work'].id).first()
        work.fingerguns = work.fingerguns + 1
        work.save()
        return fingergun


class TagSerializer(serializers.HyperlinkedModelSerializer):
    tag_type = serializers.SlugRelatedField(
        queryset=TagType.objects.all(), slug_field='label')
    tag_type_label = serializers.CharField(source='type_label', read_only=True)
    id = serializers.ReadOnlyField()

    class Meta:
        model = Tag
        fields = '__all__'

    def update(self, tag, validated_data):
        tag_type = TagType.objects.get(label=validated_data['tag_type'])
        if (tag_type.admin_administrated):
            user = validated_data['user']
            validated_data.pop('user')
            if (user.is_superuser):
                Tag.objects.filter(id=tag.id).update(**validated_data)
                return Tag.objects.filter(id=tag.id).first()
            else:
                return None
        else:
            Tag.objects.filter(id=tag.id).update(**validated_data)
            return Tag.objects.filter(id=tag.id).first()

    def create(self, validated_data):
        tag_type = TagType.objects.get(label=validated_data['tag_type'])
        if (tag_type.admin_administrated):
            user = validated_data['user']
            validated_data.pop('user')
            if (user.is_superuser):
                tag = Tag.objects.create(**validated_data)
                return tag
            else:
                return None
        tag = Tag.objects.create(**validated_data)
        return tag


class NotificationTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NotificationType
        fields = '__all__'


class OurchiveSettingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OurchiveSetting
        fields = '__all__'


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    notification_type = serializers.HyperlinkedRelatedField(
        view_name='notificationtype-detail', queryset=NotificationType.objects.all())
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    id = serializers.ReadOnlyField()

    def create(self, validated_data):
        notification = Notification.objects.create(**validated_data)
        user = User.objects.filter(id=notification.user.id).first()
        user.has_notifications = True
        user.save()
        return notification

    def update(self, notification, validated_data):
        Notification.objects.filter(
            id=notification.id).update(**validated_data)
        notification = Notification.objects.get(id=notification.id)
        unread_notifications = Notification.objects.filter(
            user__id=notification.user.id).filter(read=False).first()
        notification.user.has_notifications = unread_notifications is not None
        notification.user.save()
        return notification

    class Meta:
        model = Notification
        fields = '__all__'


class CommentUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'icon', 'icon_alt_text']


class ChapterCommentSerializer(serializers.HyperlinkedModelSerializer):
    user = CommentUserSerializer(read_only=True)
    replies = RecursiveField(many=True, required=False)
    id = serializers.ReadOnlyField()
    chapter = serializers.PrimaryKeyRelatedField(
        queryset=Chapter.objects.all(), required=False)
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=ChapterComment.objects.all(), required=False, allow_null=True)

    class Meta:
        model = ChapterComment
        fields = '__all__'

    def update(self, comment, validated_data):
        if isinstance(serializers.CurrentUserDefault(), AnonymousUser):
            validated_data.pop('user')
        ChapterComment.objects.filter(id=comment.id).update(**validated_data)
        return ChapterComment.objects.filter(id=comment.id).first()

    def create(self, validated_data):
        if 'user' in validated_data and isinstance(validated_data['user'], AnonymousUser):
            validated_data.pop('user')
        validated_data['text'] = clean_text(validated_data['text']) if validated_data['text'] is not None else ''
        comment = ChapterComment.objects.create(**validated_data)
        comment.chapter.comment_count += 1
        comment.chapter.work.comment_count += 1
        comment.chapter.save()
        comment.chapter.work.save()
        user = User.objects.filter(id=comment.chapter.user.id).first()
        notification_type = NotificationType.objects.filter(
            type_label="Comment Notification").first()
        notification = Notification.objects.create(notification_type=notification_type, user=user, title="New Chapter Comment",
                                                   content=f"""A new comment has been left on your chapter! <a href='/works/{comment.chapter.work.id}'>Click here</a> to view.""")
        notification.save()
        user.has_notifications = True
        user.save()
        return comment

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['text'] = clean_text(ret['text']) if ret['text'] is not None else ''
        return ret


class BookmarkCommentSerializer(serializers.HyperlinkedModelSerializer):
    user = CommentUserSerializer(read_only=True)
    replies = RecursiveField(many=True, required=False)
    id = serializers.ReadOnlyField()
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=BookmarkComment.objects.all(), required=False, allow_null=True)
    bookmark = serializers.PrimaryKeyRelatedField(
        queryset=Bookmark.objects.all(), required=False)

    class Meta:
        model = BookmarkComment
        fields = '__all__'

    def update(self, comment, validated_data):
        if isinstance(serializers.CurrentUserDefault(), AnonymousUser):
            validated_data.pop('user')
        BookmarkComment.objects.filter(id=comment.id).update(**validated_data)
        return BookmarkComment.objects.filter(id=comment.id).first()

    def create(self, validated_data):
        if 'user' in validated_data and isinstance(validated_data['user'], AnonymousUser):
            validated_data.pop('user')
        validated_data['text'] = clean_text(validated_data['text'])
        comment = BookmarkComment.objects.create(**validated_data)
        user = User.objects.filter(id=comment.bookmark.user.id).first()
        notification_type = NotificationType.objects.filter(
            type_label="Comment Notification").first()
        notification = Notification.objects.create(notification_type=notification_type, user=user, title="New Bookmark Comment",
                                                   content=f"""A new comment has been left on your bookmark! <a href='/bookmarks/{comment.bookmark.id}'>Click here</a> to view.""")
        notification.save()
        user.has_notifications = True
        user.save()
        comment.bookmark.comment_count = comment.bookmark.comment_count + 1
        comment.bookmark.save()
        return comment

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['text'] = clean_text(ret['text'])
        return ret


class CollectionCommentSerializer(serializers.HyperlinkedModelSerializer):
    user = CommentUserSerializer(read_only=True)
    replies = RecursiveField(many=True, required=False)
    id = serializers.ReadOnlyField()
    parent_comment = serializers.PrimaryKeyRelatedField(
        queryset=CollectionComment.objects.all(), required=False, allow_null=True)
    collection = serializers.PrimaryKeyRelatedField(
        queryset=BookmarkCollection.objects.all(), required=False)

    class Meta:
        model = CollectionComment
        fields = '__all__'

    def update(self, comment, validated_data):
        if isinstance(serializers.CurrentUserDefault(), AnonymousUser):
            validated_data.pop('user')
        CollectionComment.objects.filter(id=comment.id).update(**validated_data)
        return CollectionComment.objects.filter(id=comment.id).first()

    def create(self, validated_data):
        if 'user' in validated_data and isinstance(validated_data['user'], AnonymousUser):
            validated_data.pop('user')
        validated_data['text'] = clean_text(validated_data['text'])
        comment = CollectionComment.objects.create(**validated_data)
        user = User.objects.filter(id=comment.collection.user.id).first()
        notification_type = NotificationType.objects.filter(
            type_label="Comment Notification").first()
        notification = Notification.objects.create(notification_type=notification_type, user=user, title="New Collection Comment",
                                                   content=f"""A new comment has been left on your collection! <a href='/bookmark-collections/{comment.collection.id}'>Click here</a> to view.""")
        notification.save()
        user.has_notifications = True
        user.save()
        comment.collection.comment_count = comment.collection.comment_count + 1
        comment.collection.save()
        return comment

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['text'] = clean_text(ret['text'])
        return ret


class MessageSerializer(serializers.HyperlinkedModelSerializer):
    to_user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', format='html', read_only=False, queryset=User.objects.all())
    from_user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', format='html', read_only=True)
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', format='html', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'


class ChapterSerializer(serializers.HyperlinkedModelSerializer):
    work = serializers.PrimaryKeyRelatedField(queryset=Work.objects.all())
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', format='html', read_only=True)
    id = serializers.IntegerField(read_only=True)
    word_count = serializers.IntegerField(read_only=True)
    attributes = AttributeValueSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Chapter
        fields = '__all__'

    def validate_chapter_number(self, validated_data, chapter_id=None):
        if 'number' in validated_data and 'work' in validated_data:
            existing_number = Chapter.objects.filter(work=validated_data['work'],number=validated_data['number'])
            if existing_number:
                if chapter_id and existing_number.first().id != chapter_id:
                    raise serializers.ValidationError({"message": [f"Chapter with number {validated_data['number']} already exists. Please review chapter numbers."]})

    def update(self, chapter, validated_data):
        if 'text' in validated_data:
            validated_data['text'] = clean_text(validated_data['text']) if 'text' in validated_data and validated_data['text'] is not None else ''
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
            chapter = AttributeValueSerializer.process_attributes(chapter, validated_data, attributes)
        chapter = Chapter.objects.filter(id=chapter.id)
        if 'audio_url' in validated_data:
            if validated_data['audio_url'] is None or validated_data['audio_url'] == "None":
                validated_data['audio_url'] = ''
        self.validate_chapter_number(validated_data, chapter.first().id)
        chapter.update(**validated_data)
        Work.objects.filter(id=chapter.first().work.id).update(
            **{'zip_url': '', 'epub_url': ''})
        return chapter.first()

    def create(self, validated_data):
        validated_data['word_count'] = 0 if not (
            'text' in validated_data and validated_data['text']) else len(validated_data['text'].split())
        validated_data['text'] = clean_text(validated_data['text']) if validated_data['text'] is not None else ''
        attributes = None
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
        if 'audio_url' in validated_data:
            if validated_data['audio_url'] is None or validated_data['audio_url'] == "None":
                validated_data['audio_url'] = ''
        self.validate_chapter_number(validated_data)
        chapter = Chapter.objects.create(**validated_data)
        if attributes is not None:
            chapter = AttributeValueSerializer.process_attributes(chapter, validated_data, attributes)
        return chapter


class ChapterAllSerializer(serializers.Serializer):
    work = serializers.PrimaryKeyRelatedField(queryset=Work.objects.all())
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', format='html', read_only=True)
    id = serializers.IntegerField(read_only=True)
    number = serializers.IntegerField()
    title = serializers.ReadOnlyField()
    updated_on = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'number', 'title', 'draft', 'work', 'user', 'updated_on']


class TopTagSerializer(serializers.HyperlinkedModelSerializer):
    tag_type_label = serializers.CharField(source='type_label', read_only=True)
    id = serializers.ReadOnlyField()
    tag_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = '__all__'

    def get_tag_count(self, obj):
        tag_count = obj.work_set.count() + obj.bookmark_set.count()
        return tag_count


class WorkSerializer(serializers.HyperlinkedModelSerializer):
    tags = TagSerializer(many=True, required=False)
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    work_id = serializers.HyperlinkedIdentityField(
        view_name='work-detail', read_only=True)
    id = serializers.ReadOnlyField()
    word_count = serializers.IntegerField(read_only=True)
    audio_length = serializers.IntegerField(read_only=True)
    attributes = AttributeValueSerializer(many=True, required=False, read_only=True)
    preferred_download = serializers.ChoiceField(choices=Work.DOWNLOAD_CHOICES, required=False)
    chapter_count = serializers.IntegerField(
        source='chapters.count',
        read_only=True
    )
    work_type_name = serializers.CharField(
        source='work_type.type_name',
        read_only=True
    )
    has_drafts = serializers.SerializerMethodField()


    class Meta:
        model = Work
        fields = '__all__'

    def get_has_drafts(self, obj):
        has_drafts = obj.draft or obj.chapters.all().filter(draft=True).exists()
        return has_drafts

    def process_tags(self, work, validated_data, tags):
        tags_to_add = []
        required_tag_types = list(TagType.objects.filter(required=True))
        has_any_required = len(required_tag_types) > 0
        for item in tags:
            tag_id = unidecode.unidecode(clean_text(item['text'].lower()))
            tag_friendly_name = item['text']
            tag_type = item['tag_type']
            tag_type_id = tag_type.id
            if tag_type in required_tag_types:
                if tag_id is None or tag_id == '':
                    # todo: error
                    return None
                else:
                    required_tag_types.pop()
            try:
                tag, created = Tag.objects.get_or_create(text=tag_id, tag_type_id=tag_type_id)
            except IntegrityError:
                logger.error(f'Integrity error trying to save tag having text {tag_id} and type {tag_type_id}. Work: {work.id}')
                continue
            if tag.display_text == '':
                tag.display_text = tag_friendly_name
                tag.save()
            tags_to_add.append(tag)
        if has_any_required and len(required_tag_types) > 0:
            # todo: error
            return None
        work.tags.clear()
        for tag in tags_to_add:
            work.tags.add(tag)
        work.save()
        return work

    def update(self, work, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags') if 'tags' in validated_data else []
            work = self.process_tags(work, validated_data, tags)
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
            work = AttributeValueSerializer.process_attributes(work, validated_data, attributes)
        validated_data['word_count'] = work.word_count
        if 'summary' in validated_data:
            validated_data['summary'] = clean_text(validated_data['summary']) if validated_data['summary'] is not None else ''
        if 'notes' in validated_data:
            validated_data['notes'] = clean_text(validated_data['notes']) if validated_data['notes'] is not None else ''
        if 'cover_url' in validated_data:
            if validated_data['cover_url'] is None or validated_data['cover_url'] == "None":
                validated_data['cover_url'] = ''
        # always create a fresh file
        validated_data['epub_url'] = ''
        validated_data['zip_url'] = ''
        Work.objects.filter(id=work.id).update(**validated_data)
        return Work.objects.filter(id=work.id).first()

    def create(self, validated_data):
        tags = validated_data.pop('tags') if 'tags' in validated_data else []
        attributes = None
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
        if 'cover_url' in validated_data:
            if validated_data['cover_url'] is None or validated_data['cover_url'] == "None":
                validated_data['cover_url'] = ''
        validated_data['summary'] = clean_text(validated_data['summary']) if validated_data['summary'] is not None else ''
        validated_data['notes'] = clean_text(validated_data['notes']) if validated_data['notes'] is not None else ''
        work = Work.objects.create(**validated_data)
        work = self.process_tags(work, validated_data, tags)
        if attributes is not None:
            work = AttributeValueSerializer.process_attributes(work, validated_data, attributes)
        return work


class BookmarkWorkSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    work_link = serializers.HyperlinkedIdentityField(
        view_name='work-detail', read_only=True)
    id = serializers.ReadOnlyField()

    class Meta:
        model = Work
        fields = ['id', 'user', 'title', 'summary', 'work_link', 'cover_url', 'cover_alt_text', 'user_id']


class BookmarkSerializer(serializers.HyperlinkedModelSerializer):
    work = BookmarkWorkSerializer(required=False)
    work_id = serializers.PrimaryKeyRelatedField(queryset=Work.objects.all())
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    collection = serializers.PrimaryKeyRelatedField(queryset=BookmarkCollection.objects.all(), required=False, allow_null=True)
    bookmark_id = serializers.HyperlinkedIdentityField(
        view_name='work-detail', read_only=True)
    id = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, required=False)
    attributes = AttributeValueSerializer(many=True, required=False, read_only=True)

    # TODO: gotta be a better way to do this
    class Meta:
        model = Bookmark
        fields = '__all__'
        # if (OurchiveSetting.objects.filter(name='Ratings Enabled').first() is not None and OurchiveSetting.objects.filter(name='Ratings Enabled').first().value == 'false'):
        #    fields = [
        #        'id', 'uid', 'title', 'description', 'created_on', 'updated_on', 'draft', 'anon_comments_permitted',
        #        'comments_permitted', 'comment_count', 'public_notes', 'private_notes', 'tags',
        #        'collection', 'bookmark_id', 'user', 'attributes', 'work', 'work_id'
        #    ]
        # else:
        #    fields = '__all__'

    def process_tags(self, bookmark, validated_data, tags):
        tags_to_add = []
        required_tag_types = list(TagType.objects.filter(required=True))
        has_any_required = len(required_tag_types) > 0
        for item in tags:
            tag_id = unidecode.unidecode(clean_text(item['text'].lower()))
            tag_friendly_name = item['text']
            tag_type = item['tag_type']
            tag_type_id = TagType.objects.filter(label=tag_type).first().id
            if tag_type in required_tag_types:
                if tag_id is None or tag_id == '':
                    # todo: error
                    return None
                else:
                    required_tag_types.pop()
            try:
                tag, created = Tag.objects.get_or_create(text=tag_id, tag_type_id=tag_type_id)
            except IntegrityError:
                logger.error(f'Integrity error trying to save tag having text {tag_id} and type {tag_type_id}. Bookmark: {bookmark.id}')
                continue
            if tag.display_text == '':
                tag.display_text = tag_friendly_name
                tag.save()
            tags_to_add.append(tag)
        if has_any_required and len(required_tag_types) > 0:
            # todo: error
            return None
        bookmark.tags.clear()
        for tag in tags_to_add:
            bookmark.tags.add(tag)
        bookmark.save()
        return bookmark

    def update(self, bookmark, validated_data):
        if 'title' in validated_data and validated_data['title'] == '':
            validated_data['title'] = f'Bookmark: {bookmark.work.title}'
        if (OurchiveSetting.objects.filter(name='Ratings Enabled') and OurchiveSetting.objects.filter(name='Ratings Enabled').first().value == 'False'):
            if 'rating' in validated_data:
                validated_data.pop('rating')
        if 'description' in validated_data:
            validated_data['description'] = clean_text(validated_data['description']) if validated_data['description'] is not None else ''
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            bookmark = self.process_tags(bookmark, validated_data, tags)
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
            bookmark = AttributeValueSerializer.process_attributes(bookmark, validated_data, attributes)
        Bookmark.objects.filter(id=bookmark.id).update(**validated_data)
        return Bookmark.objects.filter(id=bookmark.id).first()

    def create(self, validated_data):
        if validated_data['work_id'].draft:
            raise serializers.ValidationError({"message": ["Cannot bookmark a draft work."]})
        if (OurchiveSetting.objects.filter(name='Ratings Enabled') and OurchiveSetting.objects.filter(name='Ratings Enabled').first().value == 'False'):
            if 'rating' in validated_data:
                validated_data.pop('rating')
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
        validated_data['description'] = clean_text(validated_data['description']) if validated_data['description'] is not None else ''
        attributes = None
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
        validated_data['work_id'] = validated_data['work_id'].id
        bookmark = Bookmark.objects.create(**validated_data)
        bookmark = self.process_tags(bookmark, validated_data, tags)
        if attributes is not None:
            bookmark = AttributeValueSerializer.process_attributes(bookmark, validated_data, attributes)
        return bookmark


class BookmarkSummarySerializer(serializers.HyperlinkedModelSerializer):
    work = serializers.SlugRelatedField(
        queryset=Work.objects.all(), slug_field='title')
    work_id = serializers.PrimaryKeyRelatedField(queryset=Work.objects.all())
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    collection = serializers.HyperlinkedRelatedField(
        view_name='bookmarkcollection-detail', queryset=BookmarkCollection.objects.all(), required=False, allow_null=True)
    bookmark_id = serializers.HyperlinkedIdentityField(
        view_name='work-detail', read_only=True)
    id = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, required=False)
    attributes = AttributeValueSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Bookmark
        fields = '__all__'


class BookmarkCollectionSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    id = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, required=False)
    attributes = AttributeValueSerializer(many=True, required=False, read_only=True)
    works = AttributeValueSerializer(many=True, required=False)
    bookmarks_readonly = BookmarkSerializer(many=True, required=False, source='bookmarks')
    bookmarks = serializers.PrimaryKeyRelatedField(queryset=Bookmark.objects.all(), required=False, many=True)

    class Meta:
        model = BookmarkCollection
        fields = '__all__'

    def update(self, bookmark, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            tags_to_add = []
            required_tag_types = list(TagType.objects.filter(required=True))
            for item in tags:
                tag_id = unidecode.unidecode(clean_text(item['text'].lower()))
                tag_friendly_name = item['text']
                tag_type = item['tag_type']
                tag_type_id = TagType.objects.filter(label=tag_type).first().id
                if tag_type in required_tag_types:
                    if tag_id is None or tag_id == '':
                        # todo: error
                        return None
                    else:
                        required_tag_types.pop()
                try:
                    tag, created = Tag.objects.get_or_create(text=tag_id, tag_type_id=tag_type_id)
                except IntegrityError:
                    logger.error(f'Integrity error trying to save tag having text {tag_id} and type {tag_type_id}. Collection: {bookmark.id}')
                    continue
                if tag.display_text == '':
                    tag.display_text = tag_friendly_name
                    tag.save()
                tags_to_add.append(tag)
            bookmark.tags.clear()
            for tag in tags_to_add:
                bookmark.tags.add(tag)
            bookmark.save()
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
            bookmark = AttributeValueSerializer.process_attributes(bookmark, validated_data, attributes)
        if 'short_description' in validated_data:
            validated_data['short_description'] = clean_text(validated_data['short_description']) if validated_data['short_description'] is not None else ''
        if 'description' in validated_data:
            validated_data['description'] = clean_text(validated_data['description']) if validated_data['description'] is not None else ''
        if 'bookmarks' in validated_data:
            bookmarks = validated_data.pop('bookmarks')
            bookmark = BookmarkCollection.objects.get(id=bookmark.id)
            bookmark.bookmarks.clear()
            for bookmark_child in bookmarks:
                if bookmark_child.draft:
                    raise serializers.ValidationError({"message": ["Cannot add draft bookmark to collection."]})
                bookmark.bookmarks.add(bookmark_child)
            bookmark.save()
        BookmarkCollection.objects.filter(
            id=bookmark.id).update(**validated_data)
        return BookmarkCollection.objects.filter(id=bookmark.id).first()

    def create(self, validated_data):
        bookmark_list = validated_data.pop('bookmarks') if 'bookmarks' in validated_data else []
        tags = []
        attributes = None
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
        if 'attributes' in validated_data:
            attributes = validated_data.pop('attributes')
        bookmark_collection = BookmarkCollection.objects.create(**validated_data)
        for item in tags:
            tag_id = unidecode.unidecode(clean_text(item['text'].lower()))
            tag_friendly_name = item['text']
            tag_type = item['tag_type']
            tag_type_id = TagType.objects.filter(label=tag_type).first().id
            try:
                tag, created = Tag.objects.get_or_create(text=tag_id, tag_type_id=tag_type_id)
            except IntegrityError:
                logger.error(f'Integrity error trying to save tag having text {tag_id} and type {tag_type_id}. Collection: {bookmark_collection.id}')
                continue
            if tag.display_text == '':
                tag.display_text = tag_friendly_name
                tag.save()
            bookmark_collection.tags.add(tag)
        for bookmark in bookmark_list:
            if bookmark.draft:
                raise serializers.ValidationError({"message": ["Cannot add draft bookmark to collection."]})
            bookmark_collection.bookmarks.add(bookmark)
        bookmark_collection.save()
        if attributes is not None:
            bookmark_collection = AttributeValueSerializer.process_attributes(bookmark_collection, validated_data, attributes)
        return bookmark_collection


class BookmarkCollectionSummarySerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='username')
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    id = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, required=False)
    attributes = AttributeValueSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = BookmarkCollection
        fields = '__all__'


class InvitationSerializer(serializers.HyperlinkedModelSerializer):
    email = UserPrivateField()

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'password', 'email', 'groups',
                  'work_set', 'bookmark_set', 'userblocks_set')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )

        user.set_password(validated_data['password'])
        user.save()
        return user


class AdminAnnouncementSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    expires_on = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = AdminAnnouncement
        fields = '__all__'
