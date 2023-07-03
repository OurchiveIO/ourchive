class WorkFilter(object):
    def __init__(self):
        self.complete = []
        self.image_formats = []
        self.tags = []
        self.audio_length_gte = []
        self.audio_length_lte = []
        self.word_count_gte = []
        self.word_count_lte = []
        self.work_type = []
        self.work_chapter_title = []
        self.work_chapter_summary = []
        self.audio_filter_gte = 'chapters__audio_length__gte'
        self.audio_filter_lte = 'chapters__audio_length__lte'
        self.image_filter = 'chapters__image_format__icontains'
        self.complete_filter = 'is_complete__exact'
        self.tag_filter = 'tags__text__icontains'
        self.word_count_gte_filter = 'word_count__gte'
        self.word_count_lte_filter = 'word_count__lte'
        self.work_type_filter = 'work_type__type_name__icontains'

    def from_dict(self, dict_obj):
        self.complete = dict_obj['complete']
        self.image_formats = dict_obj['image_formats']
        self.tags = dict_obj['tags']
        self.audio_length_gte = dict_obj['audio_length_gte']
        self.audio_length_lte = dict_obj['audio_length_lte']
        self.word_count_lte = dict_obj['word_count_lte']
        self.word_count_gte = dict_obj['word_count_gte']
        self.work_type = dict_obj['work_type']

    def to_dict(self):
        self_dict = self.__dict__
        self_dict.pop('audio_filter_lte')
        self_dict.pop('audio_filter_gte')
        self_dict.pop('complete_filter')
        self_dict.pop('tag_filter')
        self_dict.pop('image_filter')
        self_dict.pop('word_count_lte_filter')
        self_dict.pop('word_count_gte_filter')
        self_dict.pop('work_type_filter')
        return self_dict


class BookmarkFilter(object):
    def __init__(self):
        self.complete = []
        self.rating_gte = []
        self.rating_lte = []
        self.tags = []
        self.rating_filter_gte = 'rating__gte'
        self.rating_filter_lte = 'rating__lte'
        self.complete_filter = 'is_complete__exact'
        self.tag_filter = 'tags__text__icontains'

    def from_dict(self, dict_obj):
        self.complete = dict_obj['complete']
        self.rating_gte = dict_obj['rating_gte']
        self.rating_lte = dict_obj['rating_lte']
        self.tags = dict_obj['tags']

    def to_dict(self):
        self_dict = self.__dict__
        self_dict.pop('rating_filter_lte')
        self_dict.pop('rating_filter_gte')
        self_dict.pop('complete_filter')
        self_dict.pop('tag_filter')
        return self_dict


class TagFilter(object):
    def __init__(self):
        self.tag_type = []
        self.text = []
        self.tag_type_filter = 'tag_type__label__exact'
        self.text_filter = 'text__icontains'

    def from_dict(self, dict_obj):
        self.tag_type = dict_obj['tag_type']
        self.text = dict_obj['text']

    def to_dict(self):
        self_dict = self.__dict__
        self_dict.pop('tag_type_filter')
        self_dict.pop('text_filter')
        return self_dict


class CollectionFilter(object):
    def __init__(self):
        self.complete = []
        self.tags = []
        self.complete_filter = 'is_complete__exact'
        self.tag_filter = 'tags__text__icontains'
        self.attribute_filter = 'attributes__name__icontains'

    def from_dict(self, dict_obj):
        self.complete = dict_obj['complete']
        self.tags = dict_obj['tags']
        self.attributes = dict_obj['attributes']

    def to_dict(self):
        self_dict = self.__dict__
        self_dict.pop('complete_filter')
        self_dict.pop('tag_filter')
        self_dict.pop('attribute_filter')
        return self_dict


class BookmarkSearch(object):
    def __init__(self):
        self.filter = BookmarkFilter()
        self.term = ""
        self.reserved_fields = ['_state', 'uid', 'created_on', 'updated_on']
        self.term_search_fields = ['title', 'description']

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['filter'])
        self.term = dict_obj['term']

    def to_dict(self):
        self.filter = self.filter.to_dict()
        self_dict = self.__dict__
        self_dict.pop('reserved_fields')
        self_dict.pop('term_search_fields')
        return self_dict


class CollectionSearch(object):
    def __init__(self):
        self.filter = CollectionFilter()
        self.term = ""
        self.reserved_fields = ['_state', 'uid', 'created_on', 'updated_on']
        self.term_search_fields = ['title', 'short_description']

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['filter'])
        self.term = dict_obj['term']

    def to_dict(self):
        self.filter = self.filter.to_dict()
        self_dict = self.__dict__
        self_dict.pop('reserved_fields')
        self_dict.pop('term_search_fields')
        return self_dict


class TagSearch(object):
    def __init__(self):
        self.filter = TagFilter()
        self.term = ""
        self.reserved_fields = ['_state', 'uid', 'created_on', 'updated_on']
        self.term_search_fields = ['text']

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['filter'])
        self.term = dict_obj['term']

    def to_dict(self):
        self.filter = self.filter.to_dict()
        self_dict = self.__dict__
        self_dict.pop('reserved_fields')
        self_dict.pop('term_search_fields')
        return self_dict


class UserSearch(object):
    def __init__(self):
        self.filter = None
        self.term = ""
        self.reserved_fields = ['_state', 'uid', 'created_on', 'updated_on', 'password', 'is_superuser', 'first_name',
                                'last_name', 'is_staff', 'email', 'date_joined', 'last_login', 'is_active']
        self.term_search_fields = ['username']

    def from_dict(self, dict_obj):
        self.term = dict_obj['term']

    def to_dict(self):
        self.filter = self.filter
        self_dict = self.__dict__
        self_dict.pop('reserved_fields')
        self_dict.pop('term_search_fields')
        return self_dict


class WorkSearch(object):
    def __init__(self):
        self.filter = WorkFilter()
        self.term = ""
        self.reserved_fields = ['_state', 'uid', 'created_on', 'updated_on']
        self.term_search_fields = ['title', 'summary', 'chapters__title', 'chapters__summary']

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['filter'])
        self.term = dict_obj['term']

    def to_dict(self):
        self.filter = self.filter.to_dict()
        self_dict = self.__dict__
        self_dict.pop('reserved_fields')
        self_dict.pop('term_search_fields')
        return self_dict


class GlobalSearch(object):
    def __init__(self):
        self.work_search = WorkSearch().to_dict()
        self.bookmark_search = BookmarkSearch().to_dict()
        self.tag_search = TagSearch().to_dict()
        self.user_search = UserSearch().to_dict()
        self.collection_search = CollectionSearch().to_dict()

    def to_dict(self):
        return self.__dict__
