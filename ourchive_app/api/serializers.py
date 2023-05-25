from django.contrib.auth.models import User, Group, AnonymousUser
from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField
from api.models import UserProfile, Work, Tag, Chapter, TagType, WorkType, Bookmark, BookmarkCollection, ChapterComment, BookmarkComment, Message, NotificationType, Notification, OurchiveSetting, Fingergun, UserBlocks

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    id = serializers.ReadOnlyField()
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserProfileCommentSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    id = serializers.ReadOnlyField()
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'icon')

class UserBlocksSerializer(serializers.HyperlinkedModelSerializer):
    uid = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    blocked_user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    class Meta:
        model = UserBlocks
        fields = '__all__'

class UserSerializer(serializers.HyperlinkedModelSerializer):
    work_set = serializers.HyperlinkedRelatedField(many=True, view_name='work-detail', read_only=True)
    bookmark_set = serializers.HyperlinkedRelatedField(many=True, view_name='bookmark-detail', read_only=True)
    userprofile = UserProfileSerializer(read_only=True, required=False, many=False)
    userblocks_set = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name="userblocks-detail")
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'password', 'email', 'groups', 'work_set', 'bookmark_set', 'userprofile', 'userblocks_set')
        extra_kwargs = {'password': {'write_only': True}}
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )

        user.set_password(validated_data['password'])
        user.save()
        userprofile = UserProfile.objects.create(
            user=user)
        userprofile.save()
        return user
    def update(self, user, validated_data):
        validated_data['password'] = User.objects.filter(id=user.id).first().password
        User.objects.filter(id=user.id).update(**validated_data) 
        userprofile = UserProfile.objects.filter(user__id=user.id).first()
        if userprofile is None:
            userprofile = UserProfile.objects.create(
            user=user)
            userprofile.save()
        return user

class UserCommentSerializer(serializers.HyperlinkedModelSerializer):
    userprofile = UserProfileCommentSerializer(read_only=True, required=False, many=False)
    class Meta:
        model = User
        fields = ('username', 'userprofile')

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
    work = serializers.PrimaryKeyRelatedField(queryset=Work.objects.all(), required=False)
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username', required=False)
    class Meta:
        model = Fingergun
        fields = '__all__'

    def create(self, validated_data):
        # Commented out "error handling" for now. TBH, I'm not sure we want to limit this to one-per-user.
        # if (Fingergun.objects.filter(work__id=validated_data['work'].id).filter(user__id=validated_data['user'].id).all() is not None):
        #     return None
        fingergun = Fingergun.objects.create(**validated_data)
        work = Work.objects.filter(id=validated_data['work'].id).first()
        work.fingerguns = work.fingerguns + 1
        work.save()
        return fingergun

class TagSerializer(serializers.HyperlinkedModelSerializer):
    tag_type = serializers.SlugRelatedField(queryset=TagType.objects.all(), slug_field='label')
    id = serializers.ReadOnlyField()

    class Meta:
        model = Tag
        fields = '__all__'

    def update(self, tag, validated_data):
        tag_type = TagType.objects.get(label=validated_data['tag_type'])
        if (tag_type.admin_administrated):
            user = serializers.CurrentUserDefault()
            if (user.is_superuser):
                tag = Tag.objects.create(**validated_data)
                return tag
            else:
                return None
        else:
            Tag.objects.update(**validated_data)        
            return tag 

    def create(self, validated_data):
        tag_type = TagType.objects.get(label=validated_data['tag_type'])
        if (tag_type.admin_administrated):
            user = serializers.CurrentUserDefault()
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
    notification_type = serializers.HyperlinkedRelatedField(view_name='notificationtype-detail', queryset=NotificationType.objects.all())
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    id  = serializers.ReadOnlyField()
    def create(self, validated_data):
        notification = Notification.objects.create(**validated_data)
        user = User.objects.filter(id=notification.user.id).first()
        user.userprofile.has_notifications = True
        user.save()
        return notification
    def update(self, notification, validated_data):
        Notification.objects.filter(id=notification.id).update(**validated_data)  
        notification = Notification.objects.get(id=notification.id)    
        unread_notifications = Notification.objects.filter(user__id=notification.user.id).filter(read=False).first()
        user = UserProfile.objects.filter(user__id=notification.user.id).first()
        user.has_notifications = unread_notifications is not None
        user.save()
        return notification
    class Meta:
        model = Notification
        fields = '__all__'

class ReplySerializer(serializers.HyperlinkedModelSerializer):
    user = UserCommentSerializer(read_only=True)
    replies = RecursiveField(many=True, required=False)
    id = serializers.ReadOnlyField()
    class Meta:
        model = ChapterComment
        fields = '__all__'

class BookmarkReplySerializer(serializers.HyperlinkedModelSerializer):
    user = UserCommentSerializer(read_only=True)
    replies = RecursiveField(many=True, required=False)
    id = serializers.ReadOnlyField()
    class Meta:
        model = BookmarkComment
        fields = '__all__'

class ChapterCommentSerializer(serializers.HyperlinkedModelSerializer):
    user = UserCommentSerializer(read_only=True)
    replies = ReplySerializer(many=True, required=False, read_only=True)
    id = serializers.ReadOnlyField()
    chapter = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all(), required=False)
    parent_comment = serializers.PrimaryKeyRelatedField(queryset=ChapterComment.objects.all(), required=False, allow_null=True)
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
        comment = ChapterComment.objects.create(**validated_data)
        comment.chapter.comment_count += 1
        comment.chapter.work.comment_count += 1
        comment.chapter.save()
        comment.chapter.work.save()
        user = User.objects.filter(id=comment.chapter.user.id).first()
        notification = Notification.objects.create(notification_type_id=2, user=user, title="New Chapter Comment", content=f"""A new comment has been left on your chapter! <a href='/works/{comment.chapter.work.id}'>Click here</a> to view.""")     
        notification.save()
        user.userprofile.has_notifications = True
        user.userprofile.save()
        return comment

class BookmarkCommentSerializer(serializers.HyperlinkedModelSerializer):
    user = UserCommentSerializer(read_only=True)
    replies = BookmarkReplySerializer(many=True, required=False, read_only=True)
    id = serializers.ReadOnlyField()
    parent_comment = serializers.PrimaryKeyRelatedField(queryset=BookmarkComment.objects.all(), required=False, allow_null=True)
    bookmark = serializers.PrimaryKeyRelatedField(queryset=Bookmark.objects.all(), required=False)
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
        comment = BookmarkComment.objects.create(**validated_data)
        user = User.objects.filter(id=comment.bookmark.user.id).first()
        notification = Notification.objects.create(notification_type_id=2, user=user, title="New Bookmark Comment", content=f"""A new comment has been left on your bookmark! <a href='/bookmarks/{comment.bookmark.id}'>Click here</a> to view.""")     
        notification.save()
        user.userprofile.has_notifications = True
        user.userprofile.save()
        comment.bookmark.comment_count = comment.bookmark.comment_count + 1
        comment.bookmark.save()
        return comment

class MessageSerializer(serializers.HyperlinkedModelSerializer):
    to_user = serializers.HyperlinkedRelatedField(view_name='user-detail', format='html', read_only=False, queryset=User.objects.all())
    from_user = serializers.HyperlinkedRelatedField(view_name='user-detail', format='html', read_only=True)
    user = serializers.HyperlinkedRelatedField(view_name='user-detail', format='html', read_only=True)
    class Meta:
        model = Message
        fields = '__all__'

class ChapterSerializer(serializers.HyperlinkedModelSerializer):
    work = serializers.PrimaryKeyRelatedField(queryset=Work.objects.all())
    user = serializers.HyperlinkedRelatedField(view_name='user-detail', format='html', read_only=True)
    id = serializers.IntegerField(read_only=True)
    comments = ChapterCommentSerializer(many=True, required=False, read_only=True)
    word_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Chapter
        fields = '__all__'
        many = True
        partial=True

    def update_word_count(self, chapter):
        word_count = 0
        for work_chapter in chapter.work.chapters.all():
            word_count += work_chapter.word_count
        Work.objects.filter(id=chapter.work.id).update(**{'word_count': word_count})

    def update(self, chapter, validated_data):
        if 'text' in validated_data:
            validated_data['word_count'] = 0 if not validated_data['text'] else len(validated_data['text'].split())
        chapter = Chapter.objects.filter(id=chapter.id)
        chapter.update(**validated_data) 
        self.update_word_count(chapter.first())       
        return chapter.first()

    def create(self, validated_data):
        validated_data['word_count'] = 0 if not ('text' in validated_data and validated_data['text']) else len(validated_data['text'].split())
        chapter = Chapter.objects.create(**validated_data)
        self.update_word_count(chapter)
        return chapter


class WorkSerializer(serializers.HyperlinkedModelSerializer):
    tags = TagSerializer(many=True, required=False)
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    work_id = serializers.HyperlinkedIdentityField(view_name='work-detail', read_only=True)
    id = serializers.ReadOnlyField()
    word_count = serializers.IntegerField(read_only=True)
    audio_length = serializers.IntegerField(read_only=True)

    class Meta:
        model = Work
        fields = '__all__'

    def process_tags(self, work, validated_data, tags):
        work.tags.clear()
        required_tag_types = list(TagType.objects.filter(required=True))
        has_any_required = len(required_tag_types) > 0
        for item in tags:
            tag_id = item['text'].lower()
            tag_friendly_name = item['text']
            tag_type = item['tag_type']
            if tag_type in required_tag_types:
                if tag_id is None or tag_id == '':
                    # todo: error
                    return None
                else:
                    required_tag_types.pop()
            tag, created = Tag.objects.get_or_create(text=tag_id, tag_type=tag_type)
            if tag.display_text == '':
                tag.display_text = tag_friendly_name
                tag.save()
            work.tags.add(tag)
        if has_any_required and len(required_tag_types) > 0:
            #todo: error
            return None
        work.save()
        return work


    def update_word_count(self, work):
        word_count = 0
        for chapter in work.chapters.all():
            word_count += chapter.word_count
        work.word_count = word_count
        return work


    def update(self, work, validated_data):
        tags = validated_data.pop('tags') if 'tags' in validated_data else []
        work = self.process_tags(work, validated_data, tags)
        work = self.update_word_count(work)
        validated_data['word_count'] = work.word_count
        Work.objects.filter(id=work.id).update(**validated_data)        
        return Work.objects.filter(id=work.id).first()

    def create(self, validated_data):
        tags = validated_data.pop('tags') if 'tags' in validated_data else []
        work = Work.objects.create(**validated_data)
        work = self.process_tags(work, validated_data, tags)
        return work

class BookmarkSerializer(serializers.HyperlinkedModelSerializer):
    work = WorkSerializer(required=False)
    work_id = serializers.PrimaryKeyRelatedField(queryset=Work.objects.all())
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    collection = serializers.HyperlinkedRelatedField(view_name='bookmarkcollection-detail', queryset=BookmarkCollection.objects.all(), required=False, allow_null=True)
    bookmark_id = serializers.HyperlinkedIdentityField(view_name='work-detail', read_only=True)
    id = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, required=False)
    
    class Meta:
        model = Bookmark
        fields = '__all__'
    def update(self, bookmark, validated_data):
        if 'title' in validated_data and validated_data['title'] == '':
            validated_data['title'] = f'Bookmark: {bookmark.work.title}'
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            bookmark.tags.clear()
            required_tag_types = list(TagType.objects.filter(required=True))
            has_any_required = len(required_tag_types) > 0
            for item in tags:
                tag_id = item['text'].lower()
                tag_friendly_name = item['text']
                tag_type = item['tag_type']
                if tag_type in required_tag_types:
                    if tag_id is None or tag_id == '':
                        # todo: error
                        return None
                    else:
                        required_tag_types.pop()
                tag, created = Tag.objects.get_or_create(text=tag_id, tag_type=tag_type)
                if tag.display_text == '':
                    tag.display_text = tag_friendly_name
                    tag.save()
                bookmark.tags.add(tag)
            if bookmark.title == '':
                bookmark.title = bookmark.work.title
            bookmark.save()
        Bookmark.objects.filter(id=bookmark.id).update(**validated_data)        
        return Bookmark.objects.filter(id=bookmark.id).first()

    def create(self, validated_data):
        tags = validated_data.pop('tags') if 'tags' in validated_data else []
        validated_data['work_id'] = validated_data['work_id'].id
        bookmark = Bookmark.objects.create(**validated_data)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            for item in tags:
                tag_id = item['text'].lower()
                tag_friendly_name = item['text']
                tag_type = item['tag_type_id']
                tag, created = Tag.objects.get_or_create(text=tag_id, tag_type=tag_type)
                if tag.display_text == '':
                    tag.display_text = tag_friendly_name
                    tag.save()
                bookmark.tags.add(tag)
        bookmark.save()
        return bookmark

class BookmarkCollectionSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username')
    id = serializers.HyperlinkedIdentityField(view_name='bookmarkcollection-detail', read_only=True)
    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = BookmarkCollection
        fields = '__all__'
    def update(self, bookmark, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            for item in tags:
                tag_id = item['text']
                tag_type = item['tag_type_id']
                tag, created = Tag.objects.get_or_create(text=tag_id, tag_type=tag_type)
                bookmark.tags.add(tag)
            bookmark.save()
        BookmarkCollection.objects.filter(id=bookmark.id).update(**validated_data)        
        return BookmarkCollection.objects.filter(id=bookmark.id).first()

    def create(self, validated_data):
        bookmark = BookmarkCollection.objects.create(**validated_data)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            for item in tags:
                tag_id = item['text']
                tag_type = item['tag_type_id']
                tag, created = Tag.objects.get_or_create(text=tag_id, tag_type=tag_type)
                bookmark.tags.add(tag)
        bookmark.save()
        return bookmark

