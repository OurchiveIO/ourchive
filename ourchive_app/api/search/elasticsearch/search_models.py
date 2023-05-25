from datetime import datetime
from elasticsearch_dsl import Document, Date, Nested, Boolean, \
    analyzer, InnerDoc, Completion, Keyword, Text

html_strip = analyzer('html_strip',
    tokenizer="standard",
    filter=["standard", "lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)

class Comment(InnerDoc):
    user = Text(fields={'raw': Keyword()})
    text = Text()
    created_on = Date()

    def age(self):
        return datetime.now() - self.created_on

class Tag(InnerDoc):
    tag_type = Text(fields={'raw': Keyword()})
    text = Text()
    created_on = Date()

    def age(self):
        return datetime.now() - self.created_on

class Chapter(InnerDoc):
    title = Text()
    title_suggest = Completion()
    text = Text()
    summary = Text()
    audio_description = Text()
    image_alt_text = Text()
    image_size = Text()
    image_format = Text()
    created_on = Date()
    updated_on = Date()
    is_complete = Boolean()

    user = Text(fields={'raw': Keyword()})

class TagType(Document):
    label = Text()
    label_suggest = Completion()

    tags = Nested(Tag)

    class Index:
        name = 'tag'

    def save(self, ** kwargs):
        self.created_on = datetime.now()
        return super().save(** kwargs)

class Work(Document):
    title = Text()
    title_suggest = Completion()
    created_on = Date()
    updated_on = Date()
    summary = Text()
    is_complete = Boolean()

    user = Text(fields={'raw': Keyword()})

    work_type = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
    )

    tags = Nested(Tag)

    chapters = Nested(Chapter)

    class Index:
        name = 'work'

    def add_chapter(self, **kwargs):
        self.chapters.append(
          Chapter(**kwargs))

    def save(self, ** kwargs):
        self.created_on = datetime.now()
        return super().save(** kwargs)

class BookmarkNested(InnerDoc):
    title = Text()
    title_suggest = Completion()
    created_on = Date()
    updated_on = Date()
    description = Text()
    rating = Text()
    is_complete = Boolean()

    user = Text(fields={'raw': Keyword()})

    work_title = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
    )

    work_user = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
    )

    tags = Nested(Tag)

class Bookmark(Document):
    title = Text()
    title_suggest = Completion()
    created_on = Date()
    updated_on = Date()
    description = Text()
    rating = Text()
    is_complete = Boolean()

    user = Text(fields={'raw': Keyword()})

    work_title = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
    )

    work_user = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
    )

    tags = Nested(Tag)

    class Index:
        name = 'bookmark'
        
    def save(self, ** kwargs):
        self.created_on = datetime.now()
        return super().save(** kwargs)

class BookmarkCollection(Document):
    title = Text()
    title_suggest = Completion()
    is_complete = Boolean()
    created_on = Date()
    updated_on = Date()
    description = Text()
    is_complete = Boolean()

    user = Text(fields={'raw': Keyword()})

    work_type = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
    )

    tags = Nested(Tag)

    bookmarks = Nested(BookmarkNested)

    class Index:
        name = 'bookmark_collection'

    def save(self, ** kwargs):
        self.created_on = datetime.now()
        return super().save(** kwargs)


