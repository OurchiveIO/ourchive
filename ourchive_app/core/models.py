from django.db import models
from django.db.models.functions import Lower
import uuid
from django.contrib.auth.models import AbstractUser
import nh3
import unidecode
from django.utils import timezone

from .utils import clean_tag_text, count_words
from django_registration.validators import ReservedNameValidator
from django.core.validators import validate_slug
from django.conf import settings

# TODO: this feels illegal
DEFAULT_ICON_URL = f'{settings.STATIC_URL}icon-default.png'


class User(AbstractUser):
    username_validator = ReservedNameValidator()

    __tablename__ = 'user'
    id = models.AutoField(primary_key=True)
    username = models.CharField(
        "Username",
        max_length=150,
        unique=True,
        validators=[username_validator]
    )
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
    profile = models.TextField(null=True, blank=True)
    icon = models.CharField(max_length=600, null=True, blank=True, default=DEFAULT_ICON_URL)
    icon_alt_text = models.CharField(max_length=600, null=True, blank=True)
    has_notifications = models.BooleanField(default=False)
    default_content = models.TextField(null=True, blank=True)
    can_upload_audio = models.BooleanField(default=False)
    can_upload_images = models.BooleanField(default=False)
    can_upload_export_files = models.BooleanField(default=False)
    can_upload_video = models.BooleanField(default=False)
    default_post_language = models.CharField(max_length=10, blank=True, null=True)
    default_search_language = models.CharField(max_length=10, blank=True, null=True)
    default_editor = models.CharField(max_length=10, blank=True, null=True)
    attributes = models.ManyToManyField('AttributeValue', blank=True)
    display_username = models.CharField(max_length=150, blank=True, null=True)
    cookies_accepted = models.BooleanField(default=False)
    collapse_chapter_text = models.BooleanField(default=False)
    collapse_chapter_audio = models.BooleanField(default=False)
    collapse_chapter_image = models.BooleanField(default=False)
    collapse_chapter_video = models.BooleanField(default=False)
    default_work_type = models.ForeignKey('WorkType', on_delete=models.CASCADE, null=True, blank=True)
    copy_work_metadata = models.BooleanField(default=False)
    chive_export_url = models.CharField(max_length=200, blank=True, null=True)
    works = models.ManyToManyField('Work', related_name='users', through='UserWork')
    collections = models.ManyToManyField('BookmarkCollection', related_name='users', through='UserCollection')
    default_languages = models.ManyToManyField('Language', related_name='users')

    def save(self, *args, **kwargs):
        self.display_username = self.username
        self.username = self.username.lower()
        super(User, self).save(*args, **kwargs)

    class Meta:
        db_table = 'core_user'


class UserReportReason(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=200, blank=False, null=False)

    def __repr__(self):
        return '<UserReportReason: {}>'.format(self.id)

    def __str__(self):
        return self.reason

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['reason'], name='unique reportreason')]
        ordering = ['reason']
        db_table = 'core_userreportreason'


class UserReport(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
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
        db_table = 'core_userreport'


class UserSubscription(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
    subscribed_to_bookmark = models.BooleanField(default=False)
    subscribed_to_collection = models.BooleanField(default=False)
    subscribed_to_work = models.BooleanField(default=False)
    subscribed_to_series = models.BooleanField(default=False)
    subscribed_to_anthology = models.BooleanField(default=False)
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
        db_table = 'core_usersubscription'


class Language(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=200)
    ietf_code = models.CharField(max_length=40)

    def __str__(self):
        return self.display_name

    class Meta:
        db_table = 'core_language'
        constraints = [
            models.UniqueConstraint(Lower('display_name').desc(), name='unique_language_display_name')
        ]


class Work(models.Model):
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
    created_on = models.DateField(null=True, blank=True)
    updated_on = models.DateField(null=True, blank=True)
    system_created_on = models.DateTimeField(default=timezone.now)
    system_updated_on = models.DateTimeField(default=timezone.now)
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

    work_type = models.ForeignKey('WorkType', on_delete=models.SET_NULL, null=True, related_name='works')
    series = models.ForeignKey('WorkSeries', on_delete=models.SET_NULL, null=True, related_name='works')
    series_num = models.IntegerField(default=1)
    languages = models.ManyToManyField('Language')

    tags = models.ManyToManyField('Tag')

    attributes = models.ManyToManyField('AttributeValue')

    def __repr__(self):
        return '<Work: {}>'.format(self.id)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'core_work'


class UserWork(models.Model):
    id = models.AutoField(primary_key=True)
    work = models.ForeignKey(
        'Work',
        on_delete=models.CASCADE,
        related_name='work_users'
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='user_works'
    )
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        db_table = 'core_user_works'

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return '<UserWork: {}>'.format(self.id)


class WorkSeries(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    created_on = models.DateField(null=True, blank=True)
    updated_on = models.DateField(null=True, blank=True)
    system_created_on = models.DateTimeField(default=timezone.now)
    system_updated_on = models.DateTimeField(default=timezone.now)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = 'core_workseries'


class Anthology(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    is_complete = models.BooleanField(default=False)
    header_url = models.CharField(max_length=600, null=True, blank=True)
    header_alt_text = models.CharField(max_length=600, null=True, blank=True)
    cover_url = models.CharField(max_length=600, null=True, blank=True)
    cover_alt_text = models.CharField(max_length=600, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_on = models.DateField(null=True, blank=True)
    updated_on = models.DateField(null=True, blank=True)
    system_created_on = models.DateTimeField(default=timezone.now)
    system_updated_on = models.DateTimeField(default=timezone.now)
    creating_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='creating_user'
    )

    owners = models.ManyToManyField('User', through='UserAnthology')

    tags = models.ManyToManyField('Tag')
    attributes = models.ManyToManyField('AttributeValue')
    works = models.ManyToManyField('Work', related_name='anthologies', through='AnthologyWork')
    languages = models.ManyToManyField('Language')

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<Anthology: {}>'.format(self.id)

    class Meta:
        verbose_name_plural = "anthologies"
        db_table = 'core_anthology'


class AnthologyWork(models.Model):
    id = models.AutoField(primary_key=True)
    work = models.ForeignKey(
        'Work',
        on_delete=models.CASCADE,
        related_name='anthology_work'
    )
    anthology = models.ForeignKey(
        'Anthology',
        on_delete=models.CASCADE,
        related_name='work_anthology'
    )
    sort_order = models.IntegerField(default=1)

    class Meta:
        ordering = ['sort_order', 'id']
        db_table = 'core_anthology_works'

    def __str__(self):
        return f'{self.id}'

    def __repr__(self):
        return '<AnthologyWork: {}>'.format(self.id)


class UserCollection(models.Model):
    id = models.AutoField(primary_key=True)
    collection = models.ForeignKey(
        'BookmarkCollection',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='user_collections'
    )
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        db_table = 'core_user_collections'

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<UserCollection: {}>'.format(self.id)


class UserAnthology(models.Model):
    id = models.AutoField(primary_key=True)
    anthology = models.ForeignKey(
        'Anthology',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='user_anthologies'
    )
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        db_table = 'core_user_anthologies'

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<UserAnthology: {}>'.format(self.id)


class UserBlocks(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)

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

    class Meta:
        db_table = 'core_userblocks'


class Fingergun(models.Model):
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

    class Meta:
        db_table = 'core_fingergun'


class WorkType(models.Model):
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
        db_table = 'core_worktype'


class Chapter(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateField(null=True, blank=True)
    updated_on = models.DateField(null=True, blank=True)
    system_created_on = models.DateTimeField(default=timezone.now)
    system_updated_on = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=200, null=True, blank=True)
    number = models.IntegerField(default=1)
    text = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    end_notes = models.TextField(null=True, blank=True)
    word_count = models.IntegerField(default=0)
    audio_url = models.CharField(max_length=600, null=True, blank=True)
    audio_description = models.CharField(max_length=600, null=True, blank=True)
    audio_length = models.BigIntegerField(null=True, blank=True, default=0)
    video_url = models.CharField(max_length=600, null=True, blank=True)
    video_description = models.CharField(max_length=600, null=True, blank=True)
    video_length = models.BigIntegerField(null=True, blank=True, default=0)
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
            self.word_count = count_words(self.text)
        else:
            self.word_count = 0
        super(Chapter, self).save(*args, **kwargs)
        work_word_count = 0
        for work_chapter in self.work.chapters.all():
            work_word_count += work_chapter.word_count
        Work.objects.filter(id=self.work.id).update(**{'word_count': work_word_count})

    class Meta:
        ordering = ['number']
        db_table = 'core_chapter'


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.TextField()

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)

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

    class Meta:
        db_table = 'core_comment'


class BookmarkComment(Comment):
    bookmark = models.ForeignKey(
        'Bookmark',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __repr__(self):
        return '<BookmarkComment: {}>'.format(self.id)

    def save(self, *args, **kwargs):
        super(BookmarkComment, self).save(*args, **kwargs)
        self.bookmark.comment_count = BookmarkComment.objects.filter(bookmark__id=self.bookmark.id).count()
        self.bookmark.save()

    class Meta:
        db_table = 'core_bookmarkcomment'


class ChapterComment(Comment):
    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __repr__(self):
        return '<ChapterComment: {}>'.format(self.id)

    def save(self, *args, **kwargs):
        super(ChapterComment, self).save(*args, **kwargs)
        self.chapter.comment_count = ChapterComment.objects.filter(chapter__id=self.chapter.id).count()
        self.chapter.work.comment_count = ChapterComment.objects.filter(
            chapter__work__id=self.chapter.work_id).count()
        self.chapter.save()
        self.chapter.work.save()

    class Meta:
        db_table = 'core_chaptercomment'


class CollectionComment(Comment):
    collection = models.ForeignKey(
        'BookmarkCollection',
        on_delete=models.CASCADE,
        related_name='comments'
    )

    def __repr__(self):
        return '<CollectionComment: {}>'.format(self.id)

    def save(self, *args, **kwargs):
        self.collection.comment_count = CollectionComment.objects.filter(collection__id=self.collection.id).count()
        self.collection.save()
        super(CollectionComment, self).save(*args, **kwargs)

    class Meta:
        db_table = 'core_collectioncomment'


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=120, db_index=True)
    display_text = models.CharField(max_length=120, default='')
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
    filterable = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['text']),
        ]
        ordering = ('tag_type__sort_order', 'tag_type__label',)
        constraints = [
            models.UniqueConstraint(Lower('text').desc(), 'tag_type_id', name='unique_text_and_type')
        ]
        db_table = 'core_tag'

    tag_type = models.ForeignKey(
        'TagType',
        on_delete=models.CASCADE,
        related_name='tags'
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
    DEFAULT_SEARCH_GROUP_LABEL = 'Default'

    id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=200)
    type_name = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    admin_administrated = models.BooleanField(default=False)
    required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=1)
    filterable = models.BooleanField(default=True)
    show_in_aggregate = models.BooleanField(default=True)
    show_for_browse = models.BooleanField(default=False)
    search_group = models.ForeignKey(
        'SearchGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['type_name']),
        ]
        ordering = ('sort_order', 'label',)
        db_table = 'core_tagtype'

    def __repr__(self):
        return '<TagType: {}>'.format(self.id)

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        self.type_name = unidecode.unidecode(nh3.clean(self.label.lower().replace(" ", "")))
        super(TagType, self).save(*args, **kwargs)


class BookmarkCollection(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    is_complete = models.BooleanField(default=False)
    header_url = models.CharField(max_length=600, null=True, blank=True)
    header_alt_text = models.CharField(max_length=600, null=True, blank=True)
    short_description = models.CharField(max_length=300, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_on = models.DateField(null=True, blank=True)
    updated_on = models.DateField(null=True, blank=True)
    system_created_on = models.DateTimeField(default=timezone.now)
    system_updated_on = models.DateTimeField(default=timezone.now)
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
    works = models.ManyToManyField('Work')
    languages = models.ManyToManyField('Language')

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<BookmarkCollection: {}>'.format(self.id)

    class Meta:
        db_table = 'core_bookmarkcollection'


class Bookmark(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, default='', blank=True)
    rating = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    created_on = models.DateField(null=True, blank=True)
    updated_on = models.DateField(null=True, blank=True)
    system_created_on = models.DateTimeField(default=timezone.now)
    system_updated_on = models.DateTimeField(default=timezone.now)
    draft = models.BooleanField(default=False)
    anon_comments_permitted = models.BooleanField(default=True)
    comments_permitted = models.BooleanField(default=True)
    comment_count = models.IntegerField(default=0)
    public_notes = models.TextField(null=True, blank=True)
    private_notes = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)

    collection = models.ForeignKey(
        BookmarkCollection,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='bookmarks')

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    work = models.ForeignKey('Work', on_delete=models.SET_NULL, null=True)

    tags = models.ManyToManyField('Tag')
    attributes = models.ManyToManyField('AttributeValue')
    languages = models.ManyToManyField('Language')

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<Bookmark: {}>'.format(self.id)

    class Meta:
        ordering = ('id',)
        db_table = 'core_bookmark'


class BookmarkLink(models.Model):
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

    class Meta:
        db_table = 'core_bookmarklink'


class Message(models.Model):
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

    class Meta:
        db_table = 'core_message'


class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
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
        db_table = 'core_notification'


class AdminAnnouncement(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=200, default='')
    content = models.TextField(blank=True, default='')
    expires_on = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ('active', 'expires_on',)
        db_table = 'core_adminannouncement'

    def __repr__(self):
        return '<AdminAnnouncement: {}>'.format(self.id)


class News(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=200, default='')
    content = models.TextField(blank=True, default='')
    embed_in_homepage = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "news"
        db_table = 'core_news'

    def save(self, *args, **kwargs):
        self.value = nh3.clean(self.content)
        super(News, self).save(*args, **kwargs)


class NotificationType(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    type_label = models.CharField(max_length=200)
    send_email = models.BooleanField(default=False)

    def __repr__(self):
        return '<NotificationType: {}>'.format(self.id)

    def __str__(self):
        return self.type_label

    class Meta:
        db_table = 'core_notificationtype'


class Settings(models.TextChoices):
    SEARCH_PROVIDER = 'Search Provider', 'Search Provider'
    UPLOAD_ENDPOINT = 'Upload Endpoint', 'Upload Endpoint'
    REGISTRATION_PERMITTED = 'Registration Permitted', 'Registration Permitted'
    INVITE_ONLY = 'Invite Only', 'Invite Only'
    USE_INVITE_QUEUE = 'Use Invite Queue', 'Use Invite Queue'
    INVITE_QUEUE_LIMIT = 'Invite Queue Limit', 'Invite Queue Limit'
    DEFAULT_ICON_URL = 'Default Icon URL', 'Default Icon URL'
    AUDIO_PROCESSING = 'Audio Processing', 'Audio Processing'
    RATING_STAR_COUNT = 'Rating Star Count', 'Rating Star Count'
    ALLOW_COMMENTS = 'Allow Comments', 'Allow Comments'
    RATINGS_ENABLED = 'Ratings Enabled', 'Ratings Enabled'
    AUTO_ALLOW_UPLOAD = 'Auto-Allow Upload', 'Auto-Allow Upload'


class SettingsValTypes(models.TextChoices):
    TRUE_FALSE = 'truefalse', 'truefalse'
    CHOICE = 'choice', 'choice'


class OurchiveSetting(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, choices=Settings.choices)
    value = models.CharField(max_length=200)
    valtype = models.CharField(max_length=200, null=True, blank=True, choices=SettingsValTypes)
    description = models.CharField(max_length=300, null=True, blank=True)

    def __repr__(self):
        return '<OurchiveSettings: {}>'.format(self.id)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'core_ourchivesetting'


class ContentPage(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    order = models.IntegerField(default=1)
    locked_to_users = models.BooleanField(default=False)
    agree_on_signup = models.BooleanField(default=False)

    def __repr__(self):
        return '<ContentPage: {}>'.format(self.id)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order', 'id',)
        db_table = 'core_contentpage'

    def save(self, *args, **kwargs):
        self.value = nh3.clean(self.content)
        super(ContentPage, self).save(*args, **kwargs)


class Invitation(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=200)
    invite_token = models.CharField(max_length=200)
    token_expiration = models.DateTimeField(blank=True, null=True)
    token_used = models.BooleanField(default=False)
    register_link = models.CharField(max_length=200)
    approved = models.BooleanField(default=False)
    allow_upload = models.BooleanField(default=False)
    join_reason = models.TextField(max_length=400, blank=True, null=True)

    def __repr__(self):
        return '<Invitation: {}>'.format(self.id)

    class Meta:
        db_table = 'core_invitation'


class AttributeType(models.Model):
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
    allow_on_anthology = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=1)
    show_for_browse = models.BooleanField(default=False)
    search_group = models.ForeignKey(
        'SearchGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(Lower('name').desc(), name='unique_attributetype_name')
        ]
        db_table = 'core_attributetype'

    def __repr__(self):
        return '<AttributeType: {}>'.format(self.name)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(AttributeType, self).save(*args, **kwargs)


class AttributeValue(models.Model):
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
        ordering = ('attribute_type__name', 'order', 'name')
        constraints = [
            models.UniqueConstraint(Lower('name').desc(), name='unique_attributevalue_name')
        ]
        db_table = 'core_attributevalue'

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return '<AttributeValue: {}>'.format(self.name)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super(AttributeValue, self).save(*args, **kwargs)


class WorkAttribute(models.Model):
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
        db_table = 'core_workattribute'

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<AttributeValue: {}>'.format(self.id)


class BookmarkAttribute(models.Model):
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

    class Meta:
        db_table = 'core_bookmarkattribute'


class ChapterAttribute(models.Model):
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
        db_table = 'core_chapterattribute'


class UserAttribute(models.Model):
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
        db_table = 'core_userattribute'


class SearchGroup(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
    label = models.CharField(max_length=200, blank=False, null=False)
    display_order = models.IntegerField(default=1)

    def __repr__(self):
        return '<SearchGroup: {}>'.format(self.id)

    def __str__(self):
        return self.label

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['label'], name='unique label')]
        ordering = ['display_order', 'label']
