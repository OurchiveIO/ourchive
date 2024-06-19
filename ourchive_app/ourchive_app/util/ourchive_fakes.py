from random import randint

from faker import Faker
import core.models as models
import uuid


class OurchiveFakes:
    DEFAULT_LOCALES = [{'ietf_code': 'en', 'display_name': 'English'}, {'ietf_code': 'es', 'display_name': 'Spanish'}]

    def __init__(self):
        self.fake = Faker()
        self.fake.random.seed(6875309)
        self.words = set()

    def generate_unique_word(self, token=''):
        fake_word = self.fake.word()
        if fake_word in self.words:
            new_val_found = False
            fake_word = None
            while not new_val_found:
                fake_word = f'{self.fake.word()} {token}'.strip()
                new_val_found = fake_word not in self.words
        self.words.add(fake_word)
        return fake_word

    @staticmethod
    def get_random_obj(obj):
        # random record approach from https://stackoverflow.com/a/74855703
        count = obj.objects.all().count()
        random_offset = randint(0, count - 1)
        return obj.objects.all()[random_offset]

    @staticmethod
    def generate_languages(locales, persist_db=False):
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
            user = models.User(username=self.fake.email(), password=self.fake.password(length=15))
            if persist_db:
                user.save()
            users.append(user)
        return users

    def assign_fk_items(self, languages, obj, user_id, persist_db, **kwargs):
        works_count = kwargs.get('works_count', 0)
        if kwargs.get('assign_works', False):
            for y in range(0, works_count):
                obj.works.add(self.get_random_obj(models.Work))
        if kwargs.get('create_works', False):
            works = self.generate_works(user_id, works_count, persist_db)
            for work in works[0]:
                obj.works.add(work)
        tags_count = kwargs.get('tags_count', 0)
        if kwargs.get('assign_tags', False):
            for y in range(0, tags_count):
                obj.tags.add(self.get_random_obj(models.Tag))
        if kwargs.get('create_tags', False):
            tags = self.generate_tags(tags_count, persist_db, **{'create_tag_types': True})
            for tag in tags:
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
        for language in languages:
            obj.languages.add(language)
        return obj

    def generate_works(self, user_id, obj_count=1, persist_db=False, chapter_count=0, **kwargs):
        works = []
        chapters = None
        for x in range(0, obj_count):
            title = f'{self.fake.sentence()} {kwargs.get("token", "")}'.strip()
            work = models.Work(title=title,
                               summary=self.fake.paragraph(),
                               notes=self.fake.paragraph(),
                               is_complete=self.fake.pybool(),
                               cover_url=self.fake.url(),
                               cover_alt_text=self.fake.sentence(),
                               preferred_download_url=self.fake.url(),
                               anon_comments_permitted=self.fake.pybool(),
                               comments_permitted=self.fake.pybool(),
                               word_count=self.fake.pyint(max_value=300000),
                               audio_length=self.fake.pyint(),
                               fingerguns=self.fake.pyint(),
                               draft=self.fake.pybool(),
                               comment_count=self.fake.pyint(),
                               preferred_download=models.Work.DOWNLOAD_CHOICES[
                                   self.fake.pyint(max_value=len(models.Work.DOWNLOAD_CHOICES) - 1)],
                               epub_url=self.fake.url(),
                               m4b_url=self.fake.url(),
                               zip_url=self.fake.url(),
                               external_id=self.fake.pyint() if x % 2 == 0 else None,
                               user_id=user_id)
            if persist_db:
                work.save()
            if chapter_count > 0:
                chapters = []
                for y in range(1, chapter_count + 1):
                    chapter = models.Chapter(user_id=user_id,
                                             work=work,
                                             title=self.fake.words(nb=8),
                                             number=y,
                                             text=self.fake.paragraph(),
                                             notes=self.fake.paragraph(),
                                             end_notes=self.fake.paragraph(),
                                             word_count=self.fake.pyint(max_value=20000),
                                             audio_url=self.fake.url(),
                                             audio_description=self.fake.sentence(),
                                             audio_length=self.fake.pyint(),
                                             video_url=self.fake.url(),
                                             video_description=self.fake.sentence(),
                                             video_length=self.fake.pyint(),
                                             image_url=self.fake.url(),
                                             image_alt_text=self.fake.sentence(),
                                             image_format=self.fake.mime_type(),
                                             image_size=str(self.fake.pyint()),
                                             summary=self.fake.paragraph(),
                                             draft=self.fake.pybool(),
                                             comment_count=self.fake.pyint())
                    if persist_db:
                        chapter.save()
                    chapters.append(chapter)
            works.append(work)
        return works, chapters

    def generate_bookmarks(self, user_id, obj_count=1, persist_db=False, **kwargs):
        bookmarks = []
        for x in range(0, obj_count):
            title = f'{self.fake.sentence()} {kwargs.get("token", "")}'.strip()
            bookmark = models.Bookmark(title=title,
                                       description=self.fake.paragraph(),
                                       public_notes=self.fake.paragraph(),
                                       private_notes=self.fake.paragraph(),
                                       anon_comments_permitted=self.fake.pybool(),
                                       user_id=user_id,
                                       rating=0)
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
            display_text = self.generate_unique_word(kwargs.get("token", ""))
            tag = models.Tag(display_text=display_text,
                             text=display_text.lower(),
                             tag_type=tag_type)
            tags.append(tag)
            if persist_db:
                tag.save()
        return tags

    def generate_attributes(self, obj_count=1, persist_db=False, **kwargs):
        if kwargs.get('create_attribute_types', False):
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
                    A list of dicts representing languages, used when creating languages. Defaults defined in DEFAULT_LOCALES.

            """
        collections = []
        languages = []
        if kwargs.get('create_languages', False):
            languages = self.generate_languages(
                kwargs.get('locales', self.DEFAULT_LOCALES),
                persist_db
            )
        for x in range(0, obj_count):
            title = f'{self.fake.sentence()} {kwargs.get("token", "")}'.strip()
            collection = models.BookmarkCollection(title=title,
                                                   is_complete=self.fake.pybool(),
                                                   is_private=self.fake.pybool(),
                                                   short_description=self.fake.sentence(),
                                                   description=self.fake.paragraph(),
                                                   draft=self.fake.pybool(),
                                                   comments_permitted=self.fake.pybool(),
                                                   anon_comments_permitted=self.fake.pybool(),
                                                   user_id=user_id)
            if persist_db:
                collection.save()
            else:
                collection.pk = randint(0, 5000)
            collection = self.assign_fk_items(languages, collection, user_id, persist_db, **kwargs)
            collections.append(collection)
        return collections

    def generate_work_types(self, obj_count=1, persist_db=False, **kwargs):
        work_types = []
        type_names = kwargs.get('type_names', [])
        for x in range(0, obj_count):
            if not type_names:
                type_name = f'{self.fake.word()} {kwargs.get("token", "")}'.strip()
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
            display_text = f'{self.fake.word()} {kwargs.get("token", "")}'.strip()
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

    def generate_comments(self, obj_count=1, persist_db=False):
        pass

    def generate_anthologies(self, user_id, obj_count=1, persist_db=False, **kwargs):
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
                   A list of dicts representing languages, used when creating languages. Defaults defined in DEFAULT_LOCALES.

           """
        anthologies = []
        languages = []
        if kwargs.get('create_languages', False):
            languages = self.generate_languages(
                kwargs.get('locales', self.DEFAULT_LOCALES),
                persist_db
            )
        for x in range(0, obj_count):
            display_text = self.fake.sentence()
            anthology = models.Anthology(title=display_text,
                                         description=self.fake.paragraph(nb_sentences=randint(1, 12)),
                                         is_complete=self.fake.pybool(),
                                         creating_user_id=user_id)
            if persist_db:
                anthology.save()
            anthology = self.assign_fk_items(languages, anthology, user_id, persist_db, **kwargs)
            anthologies.append(anthology)
        return anthologies

    def generate_series(self, user_id, obj_count=1, persist_db=False, **kwargs):
        series_arr = []
        for x in range(0, obj_count):
            display_text = f'{self.fake.sentence()} {kwargs.get("token", "")}'.strip()
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
        pass

    def generate_announcements(self, obj_count=1, persist_db=False):
        pass

    # TODO: FINISH, AND ADD MULTI-USER SUPPORT TO ANTHOLOGIES, WORKS, COLLECTIONS