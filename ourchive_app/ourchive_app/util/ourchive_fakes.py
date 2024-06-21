from random import randint
from faker import Faker
import core.models as models
import uuid
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
DEFAULT_LOCALES = [{'ietf_code': 'en', 'display_name': 'English'}, {'ietf_code': 'es', 'display_name': 'Spanish'}]
DEFAULT_TYPE_NAMES = ['Fic', 'Podfic', 'Art', 'Vid']


class OurchiveFakes:

    def __init__(self):
        self.fake = Faker()
        self.fake.random.seed(6875309)

    def generate_everything(self, obj_count, token='', create_dependency_objs=True):
        tag_and_attribute_count = 5
        chapter_count = 6
        comment_count = 5
        reply_count = 5
        comment_depth = 2
        announcement_count = 2
        user_count = 5
        logger.info(f'Generating data. Child data will be created with limited counts. '
                    f'Tag & attribute types: {tag_and_attribute_count}. Chapters: max {chapter_count}'
                    f'Comments: max {comment_count} Replies: max {reply_count}'
                    f'Work types: {len(DEFAULT_TYPE_NAMES)}. Comment depth: {comment_depth}. '
                    f'Announcements: {announcement_count}')
        if create_dependency_objs:
            users = self.generate_users(user_count, True)
            logger.info(f'Users created. Count: {len(users)}')
            work_types = self.generate_work_types(True)
            logger.info(f'Work types created using default type names. Count: {len(work_types)}.')
            languages = self.generate_languages([], True)
            logger.info(f'Work types created using defaults. Count: {len(languages)}.')
            tag_types = self.generate_tag_types(5, True)
            logger.info(f'Tag types created. Count: {len(tag_types)}')
            attribute_types = self.generate_attribute_types(5, True)
            logger.info(f'Attribute types created. Count: {len(attribute_types)}')
            tags = self.generate_tags(obj_count * 4, True, **{'token': token})
            logger.info(f'Tags created. Count: {len(tags)}.')
            attributes = self.generate_attributes(obj_count, True, **{'token': token})
            logger.info(f'Attributes created. Count: {len(attributes)}.')
        else:
            users = models.User.objects.all()[:user_count]
        works, chapters = self.generate_works_with_varying_users(users, obj_count,
                                                                 **{'obj_count': obj_count,
                                                                    'persist_db': True,
                                                                    'chapter_count': randint(1, chapter_count),
                                                                    'token': token,
                                                                    'assign_tags': True,
                                                                    'tags_count': 20,
                                                                    'assign_attributes': True,
                                                                    'attributes_count': 10,
                                                                    'assign_languages': True,
                                                                    })
        for chapter in chapters:
            self.generate_chapter_comments(chapter.user_id, randint(0, comment_count), True,
                                           chapter,
                                           **{'reply_max': randint(0, reply_count), 'user_count': 3,
                                              'create_users': False,
                                              'comment_depth': comment_depth}
                                           )
        logger.info(f'Chapter comments created.')
        logger.info(f'Works and chapters created. Works count: {len(works)} Chapters count: {len(chapters)}')
        bookmarks = self.generate_bookmarks(users[randint(0, len(users) - 1)].id, obj_count, True, **{'token': token})
        logger.info(f'Bookmarks created. Count: {len(bookmarks)}')
        collections_opts = {
            'assign_works': True,
            'works_count': 10,
            'assign_tags': True,
            'tags_count': 20,
            'assign_attributes': True,
            'attributes_count': 10,
            'assign_languages': True,
            'token': token,
            'obj_count': obj_count
        }
        collections = self.generate_collections_with_varying_users(users, len(users), **collections_opts)
        for collection in collections:
            self.generate_collection_comments(collection.user_id, randint(0, comment_count), True,
                                              collection,
                                              **{'reply_max': randint(0, reply_count), 'user_count': 3,
                                                 'create_users': False,
                                                 'comment_depth': comment_depth}
                                              )
        logger.info(f'Collections created. Count: {len(collections)}')
        series = self.generate_series(users[randint(0, len(users) - 1)].id, obj_count, True, **{'token': token})
        logger.info(f'Series created. Count: {len(series)}')
        anthologies_opts = {
            'create_works': False,
            'assign_works': True,
            'works_count': 12,
            'create_tags': False,
            'tags_count': 15,
            'create_attributes': False,
            'attributes_count': 13,
            'assign_languages': True,
            'token': token
        }
        anthologies = self.generate_anthologies(users[randint(0, len(users) - 1)].id, obj_count, True,
                                                **anthologies_opts)
        logger.info(f'Anthologies created. Count: {len(anthologies)}')
        user_ids = []
        for x in range(0, randint(0, obj_count)):
            user_id = users[randint(0, len(users) - 1)].id
            user_ids.append(user_id)
            self.generate_notifications(user_id, randint(0, obj_count), True)
        logger.info(f'Random number of notifications created for users: {user_ids}.')
        news = self.generate_news(randint(round(obj_count / 2), obj_count), True)
        logger.info(f'News items created. Count: {len(news)}.')
        announcements = self.generate_announcements(announcement_count, True)
        logger.info(f'Announcements created. Count: {len(announcements)}.')

    def generate_unique_word(self, token=''):
        generated_word = self.fake.words(nb=1, unique=True)[0]
        fake_word = f'{generated_word}'
        if self.fake.pybool():
            fake_word = f'{fake_word} {token}'.strip()
        return fake_word

    @staticmethod
    def get_random_obj(obj):
        # random record approach from https://stackoverflow.com/a/74855703
        count = obj.objects.all().count()
        random_offset = randint(0, count - 1)
        return obj.objects.all()[random_offset]

    @staticmethod
    def generate_languages(locales=None, persist_db=False):
        if not locales:
            locales = DEFAULT_LOCALES
        languages = []
        for locale in locales:
            language = models.Language(
                ietf_code=locale.get('ietf_code'),
                display_name=locale.get('display_name'),
                uid=uuid.uuid4()
            )
            if persist_db:
                language.save()
            languages.append(language)
        return languages

    def generate_users(self, obj_count=1, persist_db=False):
        users = []
        for x in range(0, obj_count):
            user = models.User(username=self.generate_unique_word(), email=self.fake.email(),
                               password=self.fake.password(length=15))
            if persist_db:
                user.save()
            users.append(user)
        return users

    def assign_fk_items(self, obj, user_id, persist_db, languages=None, **kwargs):
        works_count = kwargs.get('works_count', 0)
        if kwargs.get('assign_works', False):
            for y in range(0, works_count):
                obj.works.add(self.get_random_obj(models.Work))
        if kwargs.get('create_works', False):
            works = self.generate_works_and_chapters(user_id, works_count, persist_db)
            for work in works[0]:
                obj.works.add(work)
        tags_count = kwargs.get('tags_count', 0)
        if kwargs.get('assign_tags', False):
            for y in range(0, tags_count):
                obj.tags.add(self.get_random_obj(models.Tag))
        if kwargs.get('create_tags', False):
            tags = self.generate_tags(tags_count, persist_db, **{'create_tag_types': True})
            for tag in tags:
                if not tag.id:
                    tag.id = randint(0, 5000)
                obj.tags.add(tag)
        attributes_count = kwargs.get('attributes_count', 0)
        if kwargs.get('assign_attributes', False):
            for y in range(0, attributes_count):
                obj.attributes.add(self.get_random_obj(models.AttributeValue))
        if kwargs.get('create_attributes', False):
            attributes = self.generate_attributes(
                attributes_count,
                persist_db,
                **{'create_attribute_types': True}
            )
            for attribute in attributes:
                obj.attributes.add(attribute)
        if kwargs.get('assign_languages', False):
            languages_count = models.Language.objects.all().count()
            for y in range(0, languages_count):
                obj.languages.add(self.get_random_obj(models.Language))
        elif kwargs.get('create_languages', False):
            for language in languages:
                obj.languages.add(language)
        obj.save()
        return obj

    def generate_works(self, user_id, obj_count, persist_db, **kwargs):
        works = []
        for x in range(0, obj_count):
            cover_url = ''
            cover_alt_text = ''
            title = f'{self.fake.sentence()}'.replace('.', '')
            if self.fake.pybool():
                title = f'{title} {kwargs.get("token", "")}'.strip()
            if self.fake.pybool() and settings.CHIVE_COVER_URLS:
                cover_image = settings.CHIVE_COVER_URLS[randint(0, len(settings.CHIVE_COVER_URLS) - 1)]
                cover_url = cover_image['cover_url']
                cover_alt_text = cover_image['cover_alt_text']
            work = models.Work(title=title,
                               summary=self.fake.paragraph(),
                               notes=self.fake.paragraph(),
                               is_complete=self.fake.pybool(),
                               cover_url=cover_url,
                               cover_alt_text=cover_alt_text,
                               anon_comments_permitted=self.fake.pybool(),
                               comments_permitted=self.fake.pybool(),
                               fingerguns=self.fake.pyint(),
                               draft=self.fake.pybool(),
                               preferred_download=models.Work.DOWNLOAD_CHOICES[
                                   self.fake.pyint(max_value=len(models.Work.DOWNLOAD_CHOICES) - 1)],
                               external_id=self.fake.pyint() if x % 2 == 0 else None,
                               user_id=user_id,
                               created_on=self.fake.date(), updated_on=self.fake.date())
            if persist_db:
                work.save()
            else:
                work.id = randint(0, 5000)
            self.assign_fk_items(work, user_id, persist_db, None, **kwargs)
            works.append(work)
        return works

    def generate_works_and_chapters(self, user_id, obj_count=1, persist_db=False, chapter_count=0, **kwargs):
        chapters = []
        works = self.generate_works(user_id, obj_count, persist_db, **kwargs)
        if chapter_count > 0:
            for work in works:
                work_chapters = self.generate_chapters(user_id, work, persist_db, chapter_count)
                chapters = chapters + work_chapters
                if persist_db:
                    work.chapters.set(work_chapters, bulk=False)
                    work.save()
        return works, chapters

    def generate_chapters(self, user_id, work, persist_db=False, chapter_count=1):
        chapters = []
        for y in range(1, chapter_count + 1):
            chapter_text = ''
            image_url = ''
            audio_url = ''
            audio_description = ''
            audio_length = 0
            image_alt_text = ''
            video_url = ''
            video_description = ''
            video_length = 0
            for z in range(1, 40):
                paragraph = self.fake.paragraph(nb_sentences=randint(5, 50))
                chapter_text = chapter_text + f' <p>{paragraph}</p>'
            if self.fake.pybool() and settings.CHAPTER_IMAGE_URLS:
                image_record = settings.CHAPTER_IMAGE_URLS[randint(0, len(settings.CHAPTER_IMAGE_URLS) - 1)]
                image_url = image_record['image_url']
                image_alt_text = image_record['image_alt_text']
            if self.fake.pybool() and settings.CHAPTER_AUDIO_URLS:
                audio_record = settings.CHAPTER_AUDIO_URLS[randint(0, len(settings.CHAPTER_AUDIO_URLS) - 1)]
                audio_url = audio_record['audio_url']
                audio_description = audio_record['audio_description']
                audio_length = audio_record['audio_length']
            if self.fake.pybool() and settings.CHAPTER_VIDEO_URLS:
                video_record = settings.CHAPTER_VIDEO_URLS[randint(0, len(settings.CHAPTER_VIDEO_URLS) - 1)]
                video_url = video_record['video_url']
                video_description = video_record['video_description']
                video_length = video_record['video_length']
            # this is done to prevent confusing & buggy looking pagination
            draft = self.fake.pybool() if ((y == 0 or y == chapter_count) and chapter_count > 2) else False
            chapter = models.Chapter(user_id=user_id,
                                     work=work,
                                     title=self.fake.sentence().replace('.', ''),
                                     number=y,
                                     text=chapter_text,
                                     notes=self.fake.paragraph(),
                                     end_notes=self.fake.paragraph(),
                                     audio_url=audio_url,
                                     audio_length=audio_length,
                                     audio_description=audio_description,
                                     video_url=video_url,
                                     video_description=video_description,
                                     video_length=video_length,
                                     image_url=image_url,
                                     image_alt_text=image_alt_text,
                                     image_format=self.fake.mime_type(),
                                     image_size=str(self.fake.pyint()),
                                     summary=self.fake.paragraph(),
                                     draft=draft,
                                     created_on=self.fake.date(), updated_on=self.fake.date())
            if persist_db:
                chapter.save()
            else:
                chapter.id = randint(0, 5000)
                chapter.system_created_on = self.fake.date_time()
            chapters.append(chapter)
        return chapters

    def generate_bookmarks(self, user_id, obj_count=1, persist_db=False, **kwargs):
        bookmarks = []
        for x in range(0, obj_count):
            title = f'{self.fake.sentence()}'.replace('.', '')
            if self.fake.pybool():
                title = f'{title} {kwargs.get("token", "")}'.strip()
            bookmark = models.Bookmark(title=title,
                                       description=self.fake.paragraph(),
                                       public_notes=self.fake.paragraph(),
                                       private_notes=self.fake.paragraph(),
                                       anon_comments_permitted=self.fake.pybool(),
                                       user_id=user_id,
                                       rating=0,
                                       created_on=self.fake.date(), updated_on=self.fake.date())
            bookmarks.append(bookmark)
            if persist_db:
                bookmark.save()
        return bookmarks

    def generate_tags(self, obj_count=1, persist_db=False, **kwargs):
        if kwargs.get('create_tag_types', False):
            self.generate_tag_types(kwargs.get('tag_type_count', 10), True)
        tags = []
        for x in range(0, obj_count):
            tag_type = self.get_random_obj(models.TagType)
            display_text = ''
            for y in range(0, 4):
                display_text = f'{display_text} {self.generate_unique_word(kwargs.get("token", ""))}'
            tag = models.Tag(display_text=display_text,
                             text=display_text.lower(),
                             tag_type=tag_type)
            tags.append(tag)
            if persist_db:
                try:
                    tag.save()
                except Exception as e:
                    print(f"Error saving tag: {e}. Some duplicates are expected.")
                    continue
        return tags

    def generate_attributes(self, obj_count=1, persist_db=False, **kwargs):
        if kwargs.get('create_attribute_types', False) and models.AttributeType.objects.count() < 1:
            self.generate_attribute_types(kwargs.get('attribute_type_count', 10), True)
        attributes = []
        for x in range(0, obj_count):
            attribute_type = self.get_random_obj(models.AttributeType)
            display_name = self.generate_unique_word(kwargs.get('token', ''))
            attribute = models.AttributeValue(display_name=display_name,
                                              name=display_name.lower(),
                                              attribute_type=attribute_type)
            attributes.append(attribute)
            if persist_db:
                attribute.save()
        return attributes

    def generate_collections(self, user_id, obj_count=1, persist_db=False, **kwargs):
        """Generates collections for testing purposes.

            Parameters
            ----------
            user_id : `int`
                The user id to assign the collections to.
            obj_count : `int`
                How many collections to generate.
            persist_db : `bool`
                If true, saves the data to the database.
            **kwargs
                token : `str`
                    A string to append to the collection's title.
                assign_works : `bool`
                   Default: false. If true, existing works are assigned to the collection.
                create_works : `bool`
                    Default: false. If true, create works and assign them to the collection.
                works_count : `int`
                    Default: 0. How many works to create or assign.
                assign_tags : `bool`
                   Default: false. If true, existing tags are assigned to the collection.
                create_tags : `bool`
                    Default: false. If true, create tags and assign them to the collection.
                tags_count : `int`
                    Default: 0. How many tags to create or assign.
                assign_attributes : `bool`
                   Default: false. If true, existing attributes are assigned to the collection.
                create_attributes : `bool`
                    Default: false. If true, create attributes and assign them to the collection.
                attributes_count : `int`
                    Default: 0. How many attributes to create or assign.
                assign_languages : `bool`
                   Default: false. If true, all existing languages are assigned to the collection.
                create_languages : `bool`
                    Default: false. If true, create languages and assign them to the collection.
                locales : `list`
                    A list of dicts representing languages. Defaults defined in DEFAULT_LOCALES.

            """
        collections = []
        languages = []
        header_url = ''
        header_alt_text = ''
        if kwargs.get('create_languages', False):
            languages = self.generate_languages(
                kwargs.get('locales', DEFAULT_LOCALES),
                persist_db
            )
        for x in range(0, obj_count):
            title = f'{self.fake.sentence()}'.replace('.', '')
            if self.fake.pybool():
                title = f'{title} {kwargs.get("token", "")}'.strip()
            if self.fake.pybool() and settings.CHIVE_HEADER_URLS:
                header_image = settings.CHIVE_HEADER_URLS[randint(0, len(settings.CHIVE_HEADER_URLS) - 1)]
                header_url = header_image['header_url']
                header_alt_text = header_image['header_alt_text']
            collection = models.BookmarkCollection(title=title,
                                                   is_complete=self.fake.pybool(),
                                                   is_private=self.fake.pybool(),
                                                   short_description=self.fake.sentence(),
                                                   header_url=header_url,
                                                   header_alt_text=header_alt_text,
                                                   description=self.fake.paragraph(),
                                                   draft=self.fake.pybool(),
                                                   comments_permitted=self.fake.pybool(),
                                                   anon_comments_permitted=self.fake.pybool(),
                                                   user_id=user_id,
                                                   created_on=self.fake.date(), updated_on=self.fake.date())
            if persist_db:
                collection.save()
                collection = self.assign_fk_items(collection, user_id, persist_db, languages, **kwargs)
            else:
                collection.pk = randint(0, 5000)
            collections.append(collection)
        return collections

    def generate_work_types(self, persist_db=False, **kwargs):
        work_types = []
        type_names = kwargs.get('type_names', DEFAULT_TYPE_NAMES)
        for x in range(0, len(type_names)):
            if not type_names:
                type_name = f'{self.fake.word()}'
                if self.fake.pybool():
                    type_name = f'{type_name} {kwargs.get("token", "")}'.strip()
            else:
                type_name = type_names[x]
            work_type = models.WorkType(type_name=type_name,
                                        sort_order=self.fake.pyint())
            work_types.append(work_type)
            if persist_db:
                work_type.save()
        return work_types

    def generate_tag_types(self, obj_count=1, persist_db=False, **kwargs):
        tag_types = []
        for x in range(0, obj_count):
            display_text = self.generate_unique_word(kwargs.get('token', ''))
            tag_type = models.TagType(label=display_text,
                                      type_name=display_text.lower())
            tag_types.append(tag_type)
            if persist_db:
                tag_type.save()
        return tag_types

    def generate_attribute_types(self, obj_count=1, persist_db=False, **kwargs):
        attribute_types = []
        for x in range(0, obj_count):
            display_name = self.generate_unique_word(kwargs.get('token', ""))
            attribute_type = models.AttributeType(display_name=display_name,
                                                  name=display_name.lower(),
                                                  allow_multiselect=self.fake.pybool(),
                                                  allow_on_user=self.fake.pybool(),
                                                  allow_on_bookmark=self.fake.pybool(),
                                                  allow_on_work=self.fake.pybool(),
                                                  allow_on_chapter=self.fake.pybool(),
                                                  allow_on_anthology=self.fake.pybool())
            attribute_types.append(attribute_type)
            if persist_db:
                attribute_type.save()
        return attribute_types

    def generate_chapter_comments(self, user_id, obj_count=1, persist_db=False, chapter=None, **kwargs):
        if not chapter:
            chapter = self.generate_works_and_chapters(user_id, 1, persist_db, 1)[1][0]
        return self.generate_comments(models.ChapterComment, 'chapter', chapter, None, obj_count, persist_db, **kwargs)

    def generate_bookmark_comments(self, user_id, obj_count=1, persist_db=False, **kwargs):
        bookmark = self.generate_bookmarks(user_id, 1, True)[0]
        return self.generate_comments(models.BookmarkComment, 'bookmark', bookmark, None, obj_count,
                                      persist_db, **kwargs)

    def generate_collection_comments(self, user_id, obj_count=1, persist_db=False, collection=None, **kwargs):
        if not collection:
            collection = self.generate_collections(user_id, 1, True)[0]
        return self.generate_comments(models.CollectionComment, 'collection', collection, None, obj_count,
                                      persist_db, **kwargs)

    def generate_comments(self, obj, fk_attr, fk_val, parent=None, obj_count=1, persist_db=False, **kwargs):
        comments = []
        reply_max = kwargs.get('reply_max', 0)
        user_count = kwargs.get('user_count', 1)
        create_users = kwargs.get('create_users', False)
        comment_depth = kwargs.get('comment_depth', 2)
        users = self.generate_users(user_count, persist_db) if create_users else []
        comment = obj()
        setattr(comment, fk_attr, fk_val)
        comment.parent_comment = parent
        kwargs['create_users'] = False
        for x in range(0, obj_count):
            text = ''
            for z in range(1, 5):
                paragraph = self.fake.paragraph(nb_sentences=randint(1, 30))
                text = text + f' <p>{paragraph}</p>'
            comment.text = text
            comment.user = users[randint(0, len(users) - 1)] if create_users else self.get_random_obj(models.User)
            if persist_db:
                comment.save()
            else:
                comment.id = randint(0, 5000)
            kwargs['comment_depth'] = comment_depth - 1
            if comment_depth < 1:
                break
            child_comments = self.generate_comments(obj, fk_attr, fk_val, comment, randint(0, reply_max),
                                                    persist_db, **kwargs)
            comment.replies.set(child_comments)
            comments.append(comment)
        return comments

    def generate_anthologies(self, user_id, obj_count=1, persist_db=False, **kwargs) -> list[models.Anthology]:
        """Generates anthologies for testing purposes.

           Parameters
           ----------
           user_id : `int`
               The user id to assign the anthologies to.
           obj_count : `int`
               How many anthologies to generate.
           persist_db : `bool`
               If true, saves the data to the database.
           **kwargs
               token : `str`
                   A string to append to the anthology's title.
               assign_works : `bool`
                  Default: false. If true, existing works are assigned to the anthology.
               create_works : `bool`
                   Default: false. If true, create works and assign them to the anthology.
               works_count : `int`
                   Default: 0. How many works to create or assign.
               assign_tags : `bool`
                  Default: false. If true, existing tags are assigned to the anthology.
               create_tags : `bool`
                   Default: false. If true, create tags and assign them to the anthology.
               tags_count : `int`
                   Default: 0. How many tags to create or assign.
               assign_attributes : `bool`
                  Default: false. If true, existing attributes are assigned to the anthology.
               create_attributes : `bool`
                   Default: false. If true, create attributes and assign them to the anthology.
               attributes_count : `int`
                   Default: 0. How many attributes to create or assign.
               assign_languages : `bool`
                  Default: false. If true, all existing languages are assigned to the anthology.
               create_languages : `bool`
                   Default: false. If true, create languages and assign them to the anthology.
               locales : `list`
                   A list of dicts representing languages. Defaults defined in DEFAULT_LOCALES.

           """
        anthologies = []
        languages = []
        if kwargs.get('create_languages', False):
            languages = self.generate_languages(
                kwargs.get('locales', DEFAULT_LOCALES),
                persist_db
            )
        for x in range(0, obj_count):
            display_text = self.fake.sentence().replace('.', '')
            anthology = models.Anthology(title=display_text,
                                         description=self.fake.paragraph(nb_sentences=randint(1, 12)),
                                         is_complete=self.fake.pybool(),
                                         creating_user_id=user_id)
            if persist_db:
                anthology.save()
            anthology = self.assign_fk_items(anthology, user_id, persist_db, languages, **kwargs)
            anthologies.append(anthology)
        return anthologies

    def generate_series(self, user_id, obj_count=1, persist_db=False, **kwargs):
        series_arr = []
        for x in range(0, obj_count):
            display_text = f'{self.fake.sentence()}'.replace('.', '')
            if self.fake.pybool():
                display_text = f'{display_text} {kwargs.get("token", "")}'.strip()
            series = models.WorkSeries(title=display_text,
                                       description=self.fake.paragraph(nb_sentences=randint(1, 12)),
                                       is_complete=self.fake.pybool(),
                                       user_id=user_id)
            if persist_db:
                series.save()
            series_arr.append(series)
        return series_arr

    def generate_notifications(self, user_id, obj_count=1, persist_db=False):
        notifications = []
        for x in range(0, obj_count):
            display_text = self.fake.sentence()
            notification = models.Notification(title=display_text,
                                               content=self.fake.paragraph(nb_sentences=2),
                                               notification_type=self.get_random_obj(models.NotificationType),
                                               read=self.fake.pybool(),
                                               user_id=user_id)
            if persist_db:
                notification.save()
            notifications.append(notification)
        return notifications

    def generate_news(self, obj_count=1, persist_db=False):
        return self.generate_news_or_announcements(models.News, obj_count, persist_db)

    def generate_announcements(self, obj_count=1, persist_db=False):
        return self.generate_news_or_announcements(models.AdminAnnouncement, obj_count, persist_db)

    def generate_news_or_announcements(self, obj, obj_count=1, persist_db=False):
        obj_items = []
        for x in range(0, obj_count):
            obj_item = obj(title=self.fake.sentence().replace('.', ''),
                           content=self.fake.paragraph(nb_sentences=3))
            obj_items.append(obj_item)
            if persist_db:
                obj_item.save()
        return obj_items

    def generate_works_with_varying_users(self, users, num_users=2, **kwargs) \
            -> tuple[list[models.Work], list[models.Chapter]]:
        works = []
        chapters = []
        chapter_count = kwargs.pop('chapter_count', 0)
        obj_count = kwargs.pop('obj_count', 0)
        persist_db = kwargs.pop('persist_db', False)
        for x in range(0, num_users):
            user_id = int(users[randint(0, len(users) - 1)].id)
            works_and_chapters = self.generate_works_and_chapters(user_id, obj_count,
                                                                  persist_db,
                                                                  chapter_count, **kwargs)
            works = works + works_and_chapters[0]
            chapters = chapters + works_and_chapters[1]
        return works, chapters

    def generate_collections_with_varying_users(self, users, num_users=2, **kwargs):
        collections = []
        obj_count = kwargs.pop('obj_count', 0)
        persist_db = kwargs.pop('persist_db', False)
        for x in range(0, num_users):
            user_id = users[randint(0, len(users) - 1)].id
            collections = collections + self.generate_collections(user_id, obj_count,
                                                                  persist_db, **kwargs)
        return collections

    def generate_works_with_cocreators(self, obj_count=1, **kwargs):
        users = self.generate_users(kwargs.get('user_count', 1), True)
        works = self.generate_works(users[0].id, obj_count, True, **kwargs)
        for work in works:
            for user in users:
                work.users.add(user)
            work.save()
        return works

    def generate_collections_with_cocreators(self, obj_count=1, **kwargs):
        users = self.generate_users(kwargs.get('user_count', 1), True)
        collections = self.generate_collections(users[0].id, obj_count, True, **kwargs)
        for collection in collections:
            for user in users:
                collection.users.add(user)
            collection.save()
        return collections

    def generate_anthologies_with_cocreators(self, obj_count=1, **kwargs):
        users = self.generate_users(kwargs.get('user_count', 1), True)
        anthologies = self.generate_anthologies(users[0].id, obj_count, True, **kwargs)
        for anthology in anthologies:
            for user in users:
                # noinspection DjangoOrm
                anthology.owners.add(user)
            anthology.save()
        return anthologies

    # TODO: support tag assignment on work
    # TODO: THEN, CREATE MANAGEMENT CONSOLE COMMAND SEEDING DATA FOR INTEGRATION TESTS
