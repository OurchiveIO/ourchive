from django.db import models
from django.db.models.functions import Lower
import uuid
from django.contrib.auth.models import User


class Work(models.Model):

    __tablename__ = 'works'

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    summary = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    process_status = models.IntegerField(null=True)
    cover_url = models.CharField(max_length=600, null=True, blank=True)
    cover_alt_text = models.CharField(max_length=600, null=True, blank=True)
    epub_id = models.CharField(max_length=600, null=True, blank=True)
    zip_id = models.CharField(max_length=600, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    anon_comments_permitted = models.BooleanField(default=True)
    comments_permitted = models.BooleanField(default=True)
    word_count = models.IntegerField(default=0)
    audio_length = models.IntegerField(default=0)
    fingerguns = models.IntegerField(default=0)
    draft = models.BooleanField(default=True)
    comment_count = models.IntegerField(default=0)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    work_type = models.ForeignKey('WorkType', on_delete=models.CASCADE,null=True)

    tags = models.ManyToManyField('Tag')

    def __repr__(self):
        return '<Work: {}>'.format(self.id)

    def __str__(self):
        return self.title


class UserBlocks(models.Model):

    __tablename__ = 'user_blocks'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    blocked_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_user'
    )

    def __str__(self):
        return str(self.uid)

    def __repr__(self):
        return '<UserBlocks: {}>'.format(self.uid)


class Fingergun(models.Model):

    __tablename__ = 'fingerguns'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)

    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return '<Fingergun: {}>'.format(self.count)

    def __str__(self):
        return self.title


class WorkType(models.Model):

    __tablename__ = 'work_types'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    type_name = models.CharField(max_length=200)

    def __repr__(self):
        return '<WorkType: {}>'.format(self.id)

    def __str__(self):
        return self.type_name


class UserProfile(models.Model):

    __tablename__ = 'userprofiles'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    profile = models.TextField(null=True, blank=True)
    icon = models.CharField(max_length=600, null=True, blank=True)
    icon_alt_text = models.CharField(max_length=600, null=True, blank=True)
    has_notifications = models.BooleanField(default=False)
    default_content = models.TextField(null=True, blank=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return '<UserProfile: {}>'.format(self.id)

    def __str__(self):
        return str(self.id)


class Chapter(models.Model):

    __tablename__ = 'chapters'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    number = models.IntegerField(default=1)
    text = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    word_count = models.IntegerField(default=0)
    audio_url = models.CharField(max_length=600, null=True, blank=True)
    audio_description = models.CharField(max_length=600, null=True, blank=True)
    audio_length = models.BigIntegerField(null=True, blank=True, default=0)
    image_url = models.CharField(max_length=600, null=True, blank=True)
    image_alt_text = models.CharField(max_length=600, null=True, blank=True)
    image_format = models.CharField(max_length=100, null=True, blank=True)
    image_size = models.CharField(max_length=100, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    draft = models.BooleanField(default=True)
    comment_count = models.IntegerField(default=0)

    work = models.ForeignKey(
        'work',
        on_delete=models.CASCADE,
        related_name='chapters'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return '<Chapter: {}>'.format(self.id)

    def __str__(self):
        return str(self.number) if self.title is None else self.title

    class Meta:
        ordering = ['number']


class BookmarkComment(models.Model):

    __tablename__ = 'bookmark_comments'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.TextField(null=True, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    parent_comment = models.ForeignKey(
        'BookmarkComment',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True
    )

    bookmark = models.ForeignKey(
        'Bookmark',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments'
    )

    def __repr__(self):
        return '<Comment: {}>'.format(self.id)

    def __str__(self):
        return self.text if self.text is not None else str(id)


class ChapterComment(models.Model):

    __tablename__ = 'chapter_comments'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.TextField(null=True, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    parent_comment = models.ForeignKey(
        'ChapterComment',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True
    )

    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments'
    )

    def __repr__(self):
        return '<Comment: {}>'.format(self.id)

    def __str__(self):
        return self.text if self.text is not None else str(id)


class Tag(models.Model):

    __tablename__ = 'tags'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=120, db_index=True)
    display_text = models.CharField(max_length=120, default='')

    class Meta:
        indexes = [
            models.Index(fields=['text']),
        ]
        ordering = ('tag_type__label',)
        constraints = [
            models.UniqueConstraint(Lower('text').desc(), 'tag_type_id', name='unique_text_and_type')
        ]

    tag_type = models.ForeignKey(
        'TagType',
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return '<Tag: {}>'.format(self.id)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        self.text = self.text.lower()
        super(Tag, self).save(*args, **kwargs)


class TagType(models.Model):

    __tablename__ = 'tag_types'
    id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=200, db_index=True)
    admin_administrated = models.BooleanField(default=False)
    required = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['label']),
        ]
        ordering = ('label',)

    def __repr__(self):
        return '<TagType: {}>'.format(self.id)

    def __str__(self):
        return self.label


class BookmarkCollection(models.Model):

    __tablename__ = 'bookmark_collection'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    is_complete = models.BooleanField(default=False)
    cover_url = models.CharField(max_length=600, null=True, blank=True)
    cover_alt_text = models.CharField(max_length=600, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    anon_comments_permitted = models.BooleanField(default=True)
    comments_permitted = models.BooleanField(default=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    is_private = models.BooleanField(default=False)

    tags = models.ManyToManyField('Tag')

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<BookmarkCollection: {}>'.format(self.id)


class Bookmark(models.Model):

    __tablename__ = 'bookmarks'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, default='', blank=True)
    rating = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    draft = models.BooleanField(default=False)
    anon_comments_permitted = models.BooleanField(default=True)
    comments_permitted = models.BooleanField(default=True)
    comment_count = models.IntegerField(default=0)

    collection = models.ForeignKey(BookmarkCollection, on_delete=models.CASCADE, null=True, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    is_private = models.BooleanField(default=False)

    work = models.ForeignKey(
        'Work',
        on_delete=models.CASCADE,
    )

    tags = models.ManyToManyField('Tag')

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<Bookmark: {}>'.format(self.id)


class BookmarkLink(models.Model):

    __tablename__ = 'bookmark_links'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    link = models.CharField(max_length=200)
    text = models.CharField(max_length=200)

    bookmark = models.ForeignKey(
        'Bookmark',
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return '<BookmarkLink: {}>'.format(self.id)


class Message(models.Model):

    __tablename__ = 'messages'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    read = models.BooleanField(default=False)

    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_recieved',
    )

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_sent',
    )

    replies = models.ManyToManyField('self')

    def __repr__(self):
        return '<Message: {}>'.format(self.id)

    def __str__(self):
        return self.subject


class Notification(models.Model):

    __tablename__ = 'notifications'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, default='')
    content = models.TextField(blank=True, default='')
    read = models.BooleanField(default=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    notification_type = models.ForeignKey(
        'NotificationType',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('read',)


class NotificationType(models.Model):
    __tablename__ = 'notification_types'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    type_label = models.CharField(max_length=200)
    send_email = models.BooleanField(default=False)

    def __repr__(self):
        return '<NotificationType: {}>'.format(self.id)

    def __str__(self):
        return self.type_label


class OurchiveSetting(models.Model):

    __tablename__ = 'ourchive_settings'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    grouping = models.CharField(max_length=200)

    def __repr__(self):
        return '<OurchiveSettings: {}>'.format(self.id)

    def __str__(self):
        return self.name


class ContentPage(models.Model):

    __tablename__ = 'ourchive_settings'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    value = models.TextField(null=True, blank=True)
    order = models.IntegerField(default=1)

    def __repr__(self):
        return '<ContentPage: {}>'.format(self.id)

    def __str__(self):
        return self.name


class Invitation(models.Model):

    __tablename__ = 'ourchive_settings'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=200)
    invite_token = models.CharField(max_length=200)
    token_expiration = models.DateTimeField()
    token_used = models.BooleanField(default=False)
    register_link = models.CharField(max_length=200)
    send_invite = models.BooleanField(default=False)

    def __repr__(self):
        return '<Invitation: {}>'.format(self.id)
