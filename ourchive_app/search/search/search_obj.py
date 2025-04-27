import unidecode
from core.utils import clean_tag_text
from search.search.constants import *

class Common():
    def get_tags(dict_obj, key='tags'):
        tags = []
        if not dict_obj.get(key):
            return tags
        for item in dict_obj.get(key):
            tags.append(clean_tag_text(item))
        return tags

    def get_completes(dict_obj):
        completes = dict_obj.get(COMPLETE_FILTER_KEY, [])
        new_completes = []
        for item in completes:
            new_completes.append(int(item))
        return new_completes


class WorkFilter(object):
    def __init__(self):
        self.include_filters = {
            'audio_length_range': {
                'ranges': [],
                'greater_than': 'chapters__audio_length__gte',
                'less_than': 'chapters__audio_length__lte',
            },
            'image_formats': {
                'chapters__image_format__icontains': [],
            },
            'complete': {
                COMPLETE_KEY: [],
            },
            'tags': {
                TAG_FILTER_KEY: [],
            },
            'attributes': {
                'attributes__display_name__icontains': [],
            },
            'word_count': {
                'word_count__lte': [],
                'word_count__gte': [],
            },
            'word_count_range': {
                'ranges': [],
                'greater_than': 'word_count__gte',
                'less_than': 'word_count__lte'
            },
            'type': {
                'work_type__type_name__icontains': []
            },
            'languages': {
                'languages__display_name__iexact': [],
            }
        }
        self.exclude_filters = {
            'audio_length_range': {
                'ranges': [],
                'greater_than': 'chapters__audio_length__gte',
                'less_than': 'chapters__audio_length__lte',
            },
            'image_formats': {
                'chapters__image_format__icontains': [],
            },
            'complete': {
                COMPLETE_KEY: [],
            },
            'tags': {
                TAG_FILTER_KEY: [],
            },
            'attributes': {
                'attributes__display_name__icontains': [],
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
            },
            'languages': {
                'languages__display_name__iexact': [],
            }
        }

    def from_dict(self, dict_obj, include=True):
        tags = Common.get_tags(dict_obj)
        completes = Common.get_completes(dict_obj)
        if include:
            self.include_filters['complete'][COMPLETE_KEY] = completes
            self.include_filters['languages']['languages__display_name__iexact'] = dict_obj.get('Language', [])
            self.include_filters['image_formats']['chapters__image_format__icontains'] = dict_obj.get('image_formats', [])
            self.include_filters['tags'][TAG_FILTER_KEY] = tags
            self.include_filters['attributes']['attributes__display_name__icontains'] = dict_obj.get('attributes', [])
            for range_tuple in dict_obj.get('audio_length_range', []):
                self.include_filters['audio_length_range']['ranges'].append(range_tuple)
            self.include_filters['word_count']['word_count__lte'] = dict_obj.get(WORD_COUNT_FILTER_KEY_LTE, [])
            self.include_filters['word_count']['word_count__gte'] = dict_obj.get(WORD_COUNT_FILTER_KEY_GTE, [])
            self.include_filters['type']['work_type__type_name__exact'] = dict_obj.get(WORK_TYPE_FILTER_KEY, [])
            for range_tuple in dict_obj.get('word_count_range', []):
                self.include_filters['word_count_range']['ranges'].append(range_tuple)
        else:
            self.exclude_filters['complete'][COMPLETE_KEY] = completes
            self.exclude_filters['languages']['languages__display_name__iexact'] = dict_obj.get('Language', [])
            self.exclude_filters['image_formats']['chapters__image_format__icontains'] = dict_obj.get('image_formats', [])
            self.exclude_filters['tags'][TAG_FILTER_KEY] = tags
            self.exclude_filters['attributes']['attributes__display_name__icontains'] = dict_obj.get('attributes', [])
            for range_tuple in dict_obj.get('audio_length_range', []):
                self.exclude_filters['audio_length_range']['ranges'].append(range_tuple)
            self.exclude_filters['word_count']['word_count__lte'] = dict_obj.get(WORD_COUNT_FILTER_KEY_LTE, [])
            self.exclude_filters['word_count']['word_count__gte'] = dict_obj.get(WORD_COUNT_FILTER_KEY_GTE, [])
            self.exclude_filters['type']['work_type__type_name__exact'] = dict_obj.get(WORK_TYPE_FILTER_KEY, [])
            for range_tuple in dict_obj.get('word_count_range', []):
                self.exclude_filters['word_count_range']['ranges'].append(range_tuple)

    def to_dict(self):
        self_dict = self.__dict__
        return self_dict


class BookmarkFilter(object):
    def __init__(self):
        self.include_filters = {
            'rating': {
                'rating__gte': [],
            },
            'attributes': {
                'attributes__display_name__icontains': [],
            },
            'tags': {
                TAG_FILTER_KEY: [],
            },
            'languages': {
                'languages__display_name__iexact': [],
            }
        }
        self.exclude_filters = {
            'rating': {
                'rating__gte': [],
            },
            'attributes': {
                'attributes__display_name__icontains': [],
            },
            'tags': {
                TAG_FILTER_KEY: [],
            },
            'languages': {
                'languages__display_name__iexact': [],
            }
        }

    def from_dict(self, dict_obj, include=True):
        tags = Common.get_tags(dict_obj)
        if include:
            self.include_filters['rating']['rating__exact'] = dict_obj.get('rating_gte', [])
            self.include_filters['languages']['languages__display_name__iexact'] = dict_obj.get('Language', [])
            self.include_filters['attributes']['attributes__display_name__icontains'] = dict_obj.get('attributes', [])
            self.include_filters['tags'][TAG_FILTER_KEY] = tags
        else:
            self.exclude_filters['rating']['rating__exact'] = dict_obj.get('rating_gte', [])
            self.exclude_filters['languages']['languages__display_name__iexact'] = dict_obj.get('Language', [])
            self.exclude_filters['attributes']['attributes__display_name__icontains'] = dict_obj.get('attributes', [])
            self.exclude_filters['tags'][TAG_FILTER_KEY] = tags

    def to_dict(self):
        self_dict = self.__dict__
        return self_dict


class TagFilter(object):
    def __init__(self):
        self.include_filters = {
            'tag_type': {
                'tag_type__label__exact': [],
            },
            'text': {
                'text__icontains': [],
            },
            'id': {
                'id__exact': [],
            }
        }
        self.exclude_filters = {
            'tag_type': {
                'tag_type__label__exact': [],
            },
            'text': {
                'text__icontains': [],
            }
        }

    def from_dict(self, dict_obj, include=True):
        tags = Common.get_tags(dict_obj, 'text')
        if include:
            self.include_filters['tag_type']['tag_type__label__exact'] = dict_obj.get('tag_type', [])
            self.include_filters['text']['text__icontains'] = tags
            self.include_filters['id']['id__exact'] = dict_obj.get('id', [])
        else:
            self.exclude_filters['tag_type']['tag_type__label__exact'] = dict_obj.get('tag_type', [])
            self.exclude_filters['text']['text__icontains'] = tags

    def to_dict(self):
        self_dict = self.__dict__
        return self_dict


class CollectionFilter(object):
    def __init__(self):
        self.include_filters = {
            'attributes': {
                'attributes__display_name__icontains': [],
            },
            'complete': {
                COMPLETE_KEY: [],
            },
            'tags': {
                TAG_FILTER_KEY: [],
            },
            'languages': {
                'languages__display_name__iexact': [],
            }
        }
        self.exclude_filters = {
            'attributes': {
                'attributes__display_name__icontains': [],
            },
            'complete': {
                COMPLETE_KEY: [],
            },
            'tags': {
                TAG_FILTER_KEY: [],
            },
            'languages': {
                'languages__display_name__iexact': [],
            }
        }

    def from_dict(self, dict_obj, include=True):
        tags = Common.get_tags(dict_obj)
        if include:
            self.include_filters['complete'][COMPLETE_KEY] = dict_obj.get('complete', [])
            self.include_filters['languages']['languages__display_name__iexact'] = dict_obj.get('Language', [])
            self.include_filters['tags'][TAG_FILTER_KEY] = tags
            self.include_filters['attributes']['attributes__display_name__icontains'] = dict_obj.get('attributes', [])
        else:
            self.exclude_filters['complete'][COMPLETE_KEY] = dict_obj.get('complete', [])
            self.exclude_filters['languages']['languages__display_name__iexact'] = dict_obj.get('Language', [])
            self.exclude_filters['tags'][TAG_FILTER_KEY] = tags
            self.exclude_filters['attributes']['attributes__display_name__icontains'] = dict_obj.get('attributes', [])

    def to_dict(self):
        self_dict = self.__dict__
        return self_dict


class BookmarkSearch(object):
    def __init__(self):
        self.filter = BookmarkFilter()
        self.term = ""
        self.reserved_fields = ['_state', 'uid', 'created_on']
        self.term_search_fields = ['title', 'description', 'tags__text', 'attributes__name']
        self.page = 1

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['include_filter'])
        self.filter.from_dict(dict_obj['exclude_filter'], False)
        if 'term' in dict_obj:
            self.term = unidecode.unidecode(dict_obj['term'])

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
        self.reserved_fields = ['_state', 'uid', 'created_on']
        self.term_search_fields = ['title', 'short_description', 'tags__text', 'attributes__name']
        self.page = 1

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['include_filter'])
        self.filter.from_dict(dict_obj['exclude_filter'], False)
        if 'term' in dict_obj:
            self.term = unidecode.unidecode(dict_obj['term'])

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
        self.page = 1

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['include_filter'])
        self.filter.from_dict(dict_obj['exclude_filter'], False)
        if 'term' in dict_obj:
            self.term = unidecode.unidecode(dict_obj['term'])

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
        self.term_search_fields = ['username', 'attributes__name']
        self.page = 1

    def from_dict(self, dict_obj):
        self.term = unidecode.unidecode(dict_obj['term'])

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
        self.reserved_fields = ['_state', 'uid', 'created_on', '_prefetched_objects_cache']
        self.term_search_fields = ['title', 'summary',
                                   'chapters__title', 'chapters__summary', 'tags__text', 'attributes__name']
        self.page = 1

    def from_dict(self, dict_obj):
        self.filter.from_dict(dict_obj['include_filter'])
        self.filter.from_dict(dict_obj['exclude_filter'], False)
        if 'term' in dict_obj:
            self.term = unidecode.unidecode(dict_obj['term'])

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
        self.options = SearchOptions().to_dict()

    def to_dict(self):
        return self.__dict__


class FilterFacet(object):
    def __init__(self, label, checked):
        self.label = label
        self.checked = checked


class ContextualFilterFacet(FilterFacet):
    def __init__(self, label, checked, inverse_checked):
        super().__init__(label, checked)
        self.inverse_checked = inverse_checked


class ResultFacet(object):
    def __init__(self, id, label, values=[], object_type=None, display_type='checkbox'):
        self.id = id
        self.label = label
        self.values = values
        self.object_type = object_type
        self.display_type = display_type

    def to_dict(self):
        self.values = [x.__dict__ for x in self.values]
        return self.__dict__

class GroupFacet(object):
    def __init__(self, id, label, facets=[]):
        self.id = id
        self.label = label
        self.facets = []

    def to_dict(self):
        self.facets = [x.__dict__ for x in self.facets]
        return self.__dict__


class SearchOptions(object):
    def __init__(self):
        self.split_include_exclude = False
        self.order_by = '-updated_on'

    def to_dict(self):
        return self.__dict__