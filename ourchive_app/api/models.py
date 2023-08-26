from django.db import models
from django.db.models.functions import Lower
import uuid
from django.contrib.auth.models import AbstractUser
import nh3
import unidecode
from .utils import clean_tag_text


class User(AbstractUser):

    __tablename__ = 'user'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    profile = models.TextField(null=True, blank=True)
    icon = models.CharField(max_length=600, null=True, blank=True)
    icon_alt_text = models.CharField(max_length=600, null=True, blank=True)
    has_notifications = models.BooleanField(default=False)
    default_content = models.TextField(null=True, blank=True)
    attributes = models.ManyToManyField('AttributeValue')
    can_upload_audio = models.BooleanField(default=False)
    can_upload_images = models.BooleanField(default=False)
    can_upload_export_files = models.BooleanField(default=False)
    default_post_language = models.CharField(max_length=10, blank=True, null=True)
    default_search_language = models.CharField(max_length=10, blank=True, null=True)
    default_editor = models.CharField(max_length=10, blank=True, null=True)
    attributes = models.ManyToManyField('AttributeValue', blank=True)
    display_username = models.CharField(max_length=150, blank=True, null=True)
    cookies_accepted = models.BooleanField(default=False)
    collapse_chapter_text = models.BooleanField(default=False)
    collapse_chapter_audio = models.BooleanField(default=False)
    collapse_chapter_image = models.BooleanField(default=False)
    default_work_type = models.ForeignKey('WorkType', on_delete=models.CASCADE,null=True, blank=True)

    def save(self, *args, **kwargs):
        self.display_username = self.username
        self.username = self.username.lower()
        super(User, self).save(*args, **kwargs)


class UserReportReason(models.Model):

    __tablename__ = 'user_report_reason'

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    reason = models.CharField(max_length=200, blank=False, null=False)

    def __repr__(self):
        return '<UserReportReason: {}>'.format(self.id)

    def __str__(self):
        return self.reason

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['reason'],name='unique reportreason')]
        ordering = ['reason']


class UserReport(models.Model):

    __tablename__ = 'user_report'

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    reason = models.ForeignKey(
        UserReportReason,
        on_delete=models.PROTECT
    )
    details = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    reported_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_user'
    )
    mod_notes = models.TextField(blank=True, null=True)
    resolved = models.BooleanField(default=False)

    def __repr__(self):
        return '<UserReport: {}>'.format(self.id)

    def __str__(self):
        return f'{self.user.username} reported {self.reported_user.username} for {self.reason.reason}'

    class Meta:
        ordering = ['resolved', '-updated_on']


class UserSubscription(models.Model):

    __tablename__ = 'user_subscription'

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    subscribed_to_bookmark = models.BooleanField(default=False)
    subscribed_to_collection = models.BooleanField(default=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    subscribed_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_user'
    )

    def __repr__(self):
        return '<UserSubscription {}>'.format(self.id)

    class Meta:
        ordering = ['-updated_on']


class Work(models.Model):

    __tablename__ = 'works'

    DOWNLOAD_CHOICES = [
        ('EPUB', 'EPUB'), ('M4B', 'M4B'), ('ZIP', 'ZIP'), ('M4A', 'M4A'),
        ('MOBI', 'MOBI')
    ]

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    summary = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    process_status = models.IntegerField(null=True)
    cover_url = models.CharField(max_length=600, null=True, blank=True)
    cover_alt_text = models.CharField(max_length=600, null=True, blank=True)
    preferred_download_url = models.CharField(max_length=600, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    anon_comments_permitted = models.BooleanField(default=True)
    comments_permitted = models.BooleanField(default=True)
    word_count = models.IntegerField(default=0)
    audio_length = models.IntegerField(default=0)
    fingerguns = models.IntegerField(default=0)
    draft = models.BooleanField(default=True)
    comment_count = models.IntegerField(default=0)
    preferred_download = models.CharField(max_length=200, blank=True, null=True, choices=DOWNLOAD_CHOICES)
    epub_url = models.CharField(max_length=600, null=True, blank=True)
    m4b_url = models.CharField(max_length=600, null=True, blank=True)
    zip_url = models.CharField(max_length=600, null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    work_type = models.ForeignKey('WorkType', on_delete=models.CASCADE,null=True)

    tags = models.ManyToManyField('Tag')

    attributes = models.ManyToManyField('AttributeValue')

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
        null=True,
        blank=True
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
    sort_order = models.IntegerField(default=1)

    def __repr__(self):
        return '<WorkType: {}>'.format(self.id)

    def __str__(self):
        return self.type_name

    class Meta:
        ordering = ['sort_order']


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
    end_notes = models.TextField(null=True, blank=True)
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

    attributes = models.ManyToManyField('AttributeValue')

    def __repr__(self):
        return '<Chapter: {}>'.format(self.id)

    def __str__(self):
        return str(self.number) if self.title is None else self.title

    def save(self, *args, **kwargs):
        if self.text:
            self.word_count = len(self.text.split())
        else:
            self.word_count = 0
        super(Chapter, self).save(*args, **kwargs)
        for work_chapter in self.work.chapters.all():
                work_word_count += work_chapter.word_count
            Work.objects.filter(id=self.work.id).update(
                **{'word_count': work_word_count})

    class Meta:
        ordering = ['number']


class Comment(models.Model):
    __tablename__ = 'comments'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.TextField(null=True, blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    parent_comment = models.ForeignKey(
        'Comment',
        on_delete=models.RESTRICT,
        related_name='replies',
        null=True,
        blank=True
    )

    def __repr__(self):
        return '<Comment: {}>'.format(self.id)

    def __str__(self):
        return self.text if self.text is not None else str(id)


class BookmarkComment(Comment):

    __tablename__ = 'bookmark_comments'

    bookmark = models.ForeignKey(
        'Bookmark',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __repr__(self):
        return '<BookmarkComment: {}>'.format(self.id)


class ChapterComment(Comment):

    __tablename__ = 'chapter_comments'

    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __repr__(self):
        return '<ChapterComment: {}>'.format(self.id)


class CollectionComment(Comment):

    __tablename__ = 'collection_comments'

    collection = models.ForeignKey(
        'BookmarkCollection',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __repr__(self):
        return '<CollectionComment: {}>'.format(self.id)


class Tag(models.Model):

    __tablename__ = 'tags'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=120, db_index=True)
    display_text = models.CharField(max_length=120, default='')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['text']),
        ]
        ordering = ('tag_type__sort_order', 'tag_type__label',)
        constraints = [
            models.UniqueConstraint(Lower('text').desc(), 'tag_type_id', name='unique_text_and_type')
        ]

    tag_type = models.ForeignKey(
        'TagType',
        on_delete=models.CASCADE,
    )

    @property
    def type_label(self):
        return self.tag_type.type_name if self.tag_type.type_name else self.tag_type.label.lower().replace(" ", "_")

    def __repr__(self):
        return '<Tag: {}>'.format(self.id)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        self.text = nh3.clean(self.text.lower())
        self.text = unidecode.unidecode(self.text)
        super(Tag, self).save(*args, **kwargs)

    def find_existing_tag(tag_text, tag_type_id):
        cleaned_text = clean_tag_text(tag_text)
        existing_tag = Tag.objects.filter(text__iexact=cleaned_text, tag_type__id=tag_type_id).first()
        return existing_tag


class TagType(models.Model):

    __tablename__ = 'tag_types'
    id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=200)
    type_name = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    admin_administrated = models.BooleanField(default=False)
    required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=['type_name']),
        ]
        ordering = ('sort_order', 'label',)

    def __repr__(self):
        return '<TagType: {}>'.format(self.id)

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        self.type_name = unidecode.unidecode(nh3.clean(self.label.lower().replace(" ", "")))
        super(TagType, self).save(*args, **kwargs)


class BookmarkCollection(models.Model):

    __tablename__ = 'bookmark_collection'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    is_complete = models.BooleanField(default=False)
    header_url = models.CharField(max_length=600, null=True, blank=True)
    header_alt_text = models.CharField(max_length=600, null=True, blank=True)
    short_description = models.CharField(max_length=300, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    draft = models.BooleanField(default=False)
    anon_comments_permitted = models.BooleanField(default=True)
    comments_permitted = models.BooleanField(default=True)
    comment_count = models.IntegerField(default=0)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    is_private = models.BooleanField(default=False)

    tags = models.ManyToManyField('Tag')
    attributes = models.ManyToManyField('AttributeValue')

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
    public_notes = models.TextField(null=True, blank=True)
    private_notes = models.TextField(null=True, blank=True)

    collection = models.ForeignKey(
        BookmarkCollection,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='bookmarks')

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

    attributes = models.ManyToManyField('AttributeValue')

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<Bookmark: {}>'.format(self.id)

    class Meta:
        ordering = ('id',)


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


class AdminAnnouncement(models.Model):

    __tablename__ = 'admin_announcements'

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, default='')
    content = models.TextField(blank=True, default='')
    expires_on = models.DateTimeField(null=True)

    def __repr__(self):
        return '<AdminAnnouncement: {}>'.format(self.id)


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
    valtype = models.CharField(max_length=200, null=True, blank=True)

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
    locked_to_users = models.BooleanField(default=False)

    def __repr__(self):
        return '<ContentPage: {}>'.format(self.id)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)

    def save(self, *args, **kwargs):
        self.value = nh3.clean(self.value)
        super(ContentPage, self).save(*args, **kwargs)


class Invitation(models.Model):

    __tablename__ = 'ourchive_settings'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=200)
    invite_token = models.CharField(max_length=200)
    token_expiration = models.DateTimeField()
    token_used = models.BooleanField(default=False)
    register_link = models.CharField(max_length=200)
    approved = models.BooleanField(default=False)
    join_reason = models.TextField(max_length=400, blank=True, null=True)

    def __repr__(self):
        return '<Invitation: {}>'.format(self.id)


class AttributeType(models.Model):

    __tablename__ = 'ourchive_settings'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    allow_on_work = models.BooleanField(default=False)
    allow_on_bookmark = models.BooleanField(default=False)
    allow_on_chapter = models.BooleanField(default=False)
    allow_on_user = models.BooleanField(default=False)
    allow_multiselect = models.BooleanField(default=True)
    allow_on_bookmark_collection = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(Lower('name').desc(), name='unique_attributetype_name')
        ]

    def __repr__(self):
        return '<AttributeType: {}>'.format(self.name)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(AttributeType, self).save(*args, **kwargs)


class AttributeValue(models.Model):

    __tablename__ = 'ourchive_settings'
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    order = models.IntegerField(default=1)

    attribute_type = models.ForeignKey(
        'AttributeType',
        on_delete=models.CASCADE,
        related_name='attribute_values'
    )

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ('attribute_type__name','order', 'name')
        constraints = [
            models.UniqueConstraint(Lower('name').desc(), name='unique_attributevalue_name')
        ]

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return '<AttributeValue: {}>'.format(self.name)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(AttributeValue, self).save(*args, **kwargs)


class WorkAttribute(models.Model):

    __tablename__ = 'work_attributes'
    id = models.AutoField(primary_key=True)
    work = models.ForeignKey(
        'Work',
        on_delete=models.CASCADE
    )
    attribute_value = models.ForeignKey(
        'AttributeValue',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<AttributeValue: {}>'.format(self.id)


class BookmarkAttribute(models.Model):

    __tablename__ = 'work_attributes'
    id = models.AutoField(primary_key=True)
    bookmark = models.ForeignKey(
        'Bookmark',
        on_delete=models.CASCADE
    )
    attribute_value = models.ForeignKey(
        'AttributeValue',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<AttributeValue: {}>'.format(self.id)


class ChapterAttribute(models.Model):

    __tablename__ = 'work_attributes'
    id = models.AutoField(primary_key=True)
    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.CASCADE
    )
    attribute_value = models.ForeignKey(
        'AttributeValue',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<AttributeValue: {}>'.format(self.id)

    class Meta:
        ordering = ['attribute_value']


class UserAttribute(models.Model):

    __tablename__ = 'user_attributes'
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE
    )
    attribute_value = models.ForeignKey(
        'AttributeValue',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<UserAttribute: {}>'.format(self.id)

    class Meta:
        ordering = ['attribute_value']
