class WorkFilter(object):
    def __init__(self):
        self.filters = {
            'audio_length_range': {
                'ranges': [],
                'greater_than': 'chapters__audio_length__gte',
                'less_than': 'chapters__audio_length__lte',
            },
            'image_formats': {
                'chapters__image_format__icontains': [],
            },
            'complete': {
                'is_complete__exact': [],
            },
            'tags': {
                'tags__text__icontains': [],
            },
            'word_count': {
                'word_count__gte': [],
                'word_count__lte': [],
            },
            'word_count_range': {
                'ranges': [],
                'greater_than': 'word_count__gte',
                'less_than': 'word_count__lte'
            },
            'type': {
                'work_type__type_name__icontains': []
            }
        }

    def from_dict(self, dict_obj):
        self.filters['complete']['is_complete__exact'] = dict_obj.get('complete', [])
        self.filters['image_formats']['chapters__image_format__icontains'] = dict_obj.get('image_formats', [])
        self.filters['tags']['tags__text__icontains'] = dict_obj.get('tags', [])
        for range_tuple in dict_obj.get('audio_length_range', []):
            self.filters['audio_length_range']['ranges'].append(range_tuple)
        self.filters['word_count']['word_count__lte'] = dict_obj.get('word_count_lte', [])
        self.filters['word_count']['word_count__gte'] = dict_obj.get('word_count_gte', [])
        self.filters['type']['work_type__type_name__icontains'] = dict_obj.get('work_type', [])
        for range_tuple in dict_obj.get('word_count_range', []):
            self.filters['word_count_range']['ranges'].append(range_tuple)

    def to_dict(self):
        self_dict = self.__dict__
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
        self.term_search_fields = ['title', 'summary',
                                   'chapters__title', 'chapters__summary']

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
