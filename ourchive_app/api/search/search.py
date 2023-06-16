from api.models import Work, Tag, User, Chapter, TagType, WorkType, Bookmark, BookmarkComment, ChapterComment, Message, NotificationType, Notification, OurchiveSetting
from api import object_factory
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
import json
from psycopg2.extensions import adapt
import re
from django.db.models import Q
from .search_obj import WorkSearch, BookmarkSearch, TagSearch, UserSearch

class ElasticSearchProvider:
	from elasticsearch import Elasticsearch
	from elasticsearch_dsl import Search, Q
	def init_provider():
		print('init provider')
	def search_works(self, **kwargs):
		q = Q("multi_match", query=kwargs['filter']['term'], fields=['title', 'summary', 'chapter__title', 'chapters__summary', 'tags__text'])
		filters = kwargs['filter']

		client = Elasticsearch()

		s = Search(using=client, index="work")
		if 'complete' in filters:
			s = s.filter("term", is_complete=True)
		if 'audio_length' in filters:
			s = s.filter("range", chapters__audio_length={
                        "gt": filters['audio_length']
                    })
		if 'image_formats' in filters:
			s = s.filter("terms", chapters__image_format=filters['image_formats'])
		if 'image_formats' in filters:
			s = s.filter("terms", tags__text_format=filters['tags'])
		s = s.query(q)
		response = s.execute()
		return response

	def search_bookmarks(self, **kwargs):
		print('search bookmarks')
	def search_users(self, **kwargs):
		print('search users')
	def search_tags(self, **kwargs):
		print('search users')

class ElasticSearchServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, port, **_ignored):
        if not self._instance:
            self._instance = ElasticSearchProvider()
        return self._instance

class PostgresProvider:

	# ref: https://www.julienphalip.com/blog/adding-search-to-a-django-site-in-a-snap/
	def normalize_query(self, query_string,
	                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
	                    normspace=re.compile(r'\s{2,}').sub):
	    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
	        and grouping quoted words together.
	        Example:

	        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
	        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

	    '''
	    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

	def get_query(self, query_string, search_fields):
	    ''' Returns a query, that is a combination of Q objects. That combination
	        aims to search keywords within a model by testing the given search fields.

	    '''
	    query = None # Query to search for every search term        
	    terms = self.normalize_query(query_string)
	    for term in terms:
	        or_query = None # Query to search for a given term in each field
	        for field_name in search_fields:
	            q = Q(**{"%s__icontains" % field_name: term})
	            if or_query is None:
	                or_query = q
	            else:
	                or_query = or_query | q
	        if query is None:
	            query = or_query
	        else:
	            query = query & or_query
	    return query

	def build_filter_query(self, filter_array, filter_text, existing_query):
		if len(filter_array) > 0:
			or_query = None
			for array_item in filter_array:
				q = Q(**{filter_text: array_item})
				if or_query is None:
					or_query = q
				else:
					or_query = or_query | q
			if existing_query is None:
				existing_query = or_query
			else:
				existing_query = existing_query & or_query
		return existing_query
	
	def init_provider():
		print('init provider')

	def search_works(self, **kwargs):
		work_search = WorkSearch()
		work_search.from_dict(kwargs)
		work_filters = None
		work_filters = self.build_filter_query(work_search.filter.complete, work_search.filter.complete_filter, work_filters)
		work_filters = self.build_filter_query(work_search.filter.audio_length_gte, work_search.filter.audio_filter_gte, work_filters)
		work_filters = self.build_filter_query(work_search.filter.audio_length_lte, work_search.filter.audio_filter_lte, work_filters)
		work_filters = self.build_filter_query(work_search.filter.image_formats, work_search.filter.image_filter, work_filters)
		work_filters = self.build_filter_query(work_search.filter.tags, work_search.filter.tag_filter, work_filters)
		work_filters = self.build_filter_query(work_search.filter.word_count_gte, work_search.filter.word_count_gte_filter, work_filters)
		work_filters = self.build_filter_query(work_search.filter.word_count_lte, work_search.filter.word_count_lte_filter, work_filters)
		work_filters = self.build_filter_query(work_search.filter.work_type, work_search.filter.work_type_filter, work_filters)
		# todo work type	
		query = self.get_query(work_search.term, work_search.term_search_fields)
		resultset = None
		if work_filters is not None and query is not None:
			resultset = Work.objects.filter(work_filters).filter(query)
		elif work_filters is not None:
			resultset = Work.objects.filter(work_filters)
		elif query is not None:
			resultset = Work.objects.filter(query)
		result_json = []
		if resultset is None:
			return result_json
		for result in resultset:
			username = result.user.username
			tags = []
			for tag in result.tags.all():
				tag_dict = {}
				tag_dict["tag_type"] = tag.tag_type.label
				tag_dict["text"] = tag.text
				tags.append(tag_dict)
			work_type = None if result.work_type is None else result.work_type.type_name
			result_dict = result.__dict__
			for field in work_search.reserved_fields:
				result_dict.pop(field, None)
			result_dict["user"] = username
			result_dict["work_type"] = work_type
			result_dict["tags"] = tags
			result_json.append(result_dict)
		return result_json

	def search_bookmarks(self, **kwargs):
		bookmark_search = BookmarkSearch()
		bookmark_search.from_dict(kwargs)
		bookmark_filters = None
		bookmark_filters = self.build_filter_query(bookmark_search.filter.complete, bookmark_search.filter.complete_filter, bookmark_filters)
		bookmark_filters = self.build_filter_query(bookmark_search.filter.rating_gte, bookmark_search.filter.rating_filter_gte, bookmark_filters)
		bookmark_filters = self.build_filter_query(bookmark_search.filter.rating_lte, bookmark_search.filter.rating_filter_lte, bookmark_filters)
		bookmark_filters = self.build_filter_query(bookmark_search.filter.tags, bookmark_search.filter.tag_filter, bookmark_filters)

		query = self.get_query(bookmark_search.term, bookmark_search.term_search_fields)
		resultset = None
		if bookmark_filters is not None and query is not None:
			resultset = Bookmark.objects.filter(bookmark_filters).filter(query)
		elif bookmark_filters is not None:
			resultset = Bookmark.objects.filter(bookmark_filters)
		else:
			resultset = Bookmark.objects.filter(query)
		result_json = []
		for result in resultset:
			username = result.user.username
			tags = []
			for tag in result.tags.all():
				tag_dict = {}
				tag_dict["tag_type"] = tag.tag_type.label
				tag_dict["text"] = tag.text
				tags.append(tag_dict)
			result_dict = result.__dict__
			result_dict["tags"] = tags
			result_dict["user"] = username	
			for field in bookmark_search.reserved_fields:
				result_dict.pop(field, None)
			result_json.append(result_dict)
		return result_json

	def search_users(self, **kwargs):
		user_search = UserSearch()
		user_search.from_dict(kwargs)
		query = self.get_query(user_search.term, user_search.term_search_fields)
		if query is None:
			return []
		resultset = User.objects.filter(is_active=True).filter(query)
		result_json = []
		for result in resultset:
			result_dict = result.__dict__
			for field in user_search.reserved_fields:
				result_dict.pop(field, None)
			result_json.append(result_dict)
		return result_json

	def autocomplete_tags(self, term, tag_type, fetch_all=False):
		results = []
		resultset = None
		term = term.lower()
		if tag_type:
			resultset = Tag.objects.filter(tag_type__label=tag_type).filter(text__contains=term)
		else:
			resultset = Tag.objects.filter(text__contains=term)
		if resultset is None:
			resultset = Tag.objects.filter(tag_type__label=tag_type) if fetch_all else []
		for result in resultset:
			results.append({"tag": result.text, "display_text": result.display_text, "id": result.id, "type": result.tag_type.label})
		return results

	def autocomplete_bookmarks(self, term, user):
		results = []
		resultset = None
		term = term.lower()
		resultset = Bookmark.objects.filter(user__id=user).filter(Q(title__icontains=term) | Q(work__title__icontains=term)).prefetch_related('work')
		for result in resultset:
			work_dict = vars(result.work)
			if '_state' in work_dict:
				work_dict.pop('_state')
			bookmark_dict = vars(result)
			if '_state' in bookmark_dict:
				bookmark_dict.pop('_state')
			bookmark_dict['work'] = work_dict
			results.append({"bookmark": bookmark_dict})
		return results

	def search_tags(self, **kwargs):
		tag_search = TagSearch()
		tag_search.from_dict(kwargs)
		tag_filters = None
		tag_filters = self.build_filter_query(tag_search.filter.tag_type, tag_search.filter.tag_type_filter, tag_filters)
		tag_filters = self.build_filter_query(tag_search.filter.text, tag_search.filter.text_filter, tag_filters)

		query = self.get_query(tag_search.term, tag_search.term_search_fields)
		resultset = None
		if tag_filters is not None and query is not None:
			resultset = Tag.objects.filter(tag_filters).filter(query)
		elif tag_filters is not None:
			resultset = Tag.objects.filter(tag_filters)
		elif query is not None:
			resultset = Tag.objects.filter(query)
		result_json = []
		if resultset is None:
			return result_json
		for result in resultset:
			tag_type = result.tag_type.label
			result_dict = result.__dict__
			for field in tag_search.reserved_fields:
				result_dict.pop(field, None)
			result_dict['tag_type'] = tag_type
			result_json.append(result_dict)
		return result_json

	def get_result_facets(self, results):
		result_json = []
		work_types = WorkType.objects.all()
		work_types_list = []
		for work_type in work_types:
			work_types_list.append({"label": work_type.type_name, "filter_val": "work_type$"+work_type.type_name})
		work_types_dict = {}
		work_types_dict["label"] = "Work Type"
		work_types_dict["values"] = work_types_list
		result_json.append(work_types_dict)

		## todo move to db setting
		word_count_dict = {}
		word_count_dict["label"] = "Word Count"
		word_count_dict["values"] = [{"label": "Under 20,000", "filter_val": "word_count_lte$20000"},
		{"label": "20,000 - 50,000", "filter_val": "word_count_lte$50000|word_count_gte$20000"}, 
		{"label": "50,000 - 80,000", "filter_val": "word_count_lte$80000|word_count_gte$50000"}, 
		{"label": "80,000 - 100,000", "filter_val": "word_count_lte$100000|word_count_gte$80000"},
		{"label": "100,000+", "filter_val": "word_count_gte$100000"}]
		result_json.append(word_count_dict)

		## todo move to db setting
		audio_length_dict = {}
		audio_length_dict["label"] = "Audio Length"
		audio_length_dict["values"] = [{"label": "Under 30:00", "filter_val": "audio_length_gte$30"},
		{"label": "30:00 - 1:00:00", "filter_val": "audio_length_lte$60|audio_length_gte$30"}, 
		{"label": "1:00:00 - 2:00:00", "filter_val": "audio_length_lte$120|audio_length_gte$60"}, 
		{"label": "2:00:00 - 3:00:00", "filter_val": "audio_length_lte$180|audio_length_gte$120"},
		{"label": "3:00:00+", "filter_val": "audio_length_gte$180"}]
		result_json.append(audio_length_dict)

		## todo move to db setting
		complete_dict = {}
		complete_dict["label"] = "Complete?"
		complete_dict["values"] = [{"label": "Complete", "filter_val": "complete$1"},
		{"label": "Work In Progress", "filter_val": "complete$0"}]
		result_json.append(complete_dict)

		tags_dict = {}
		for tag_type in TagType.objects.all():
			tags_dict[tag_type.label] = []
		for result in results['work']:
			if len(result['tags']) > 0:
				for tag in result['tags']:
					if tag['text'] not in tags_dict[tag['tag_type']]:
						tags_dict[tag['tag_type']].append(tag['text'])
		for result in results['bookmark']:
			if len(result['tags']) > 0:
				for tag in result['tags']:
					if tag['text'] not in tags_dict[tag['tag_type']]:
						tags_dict[tag['tag_type']].append(tag['text'])
		for result in results['tag']:
			if result['text'] not in tags_dict[result['tag_type']]:
				tags_dict[result['tag_type']].append(result['text'])
		for key in tags_dict:
			if len(tags_dict[key]) > 0:
				tag_filter_vals = []
				for val in tags_dict[key]:
					filter_val = "tag_type," + str(key) + "$tag_text," + val
					tag_filter_vals.append({"label": val, "filter_val": filter_val})
				result_json.append({'label': key, 'values': tag_filter_vals})

		bookmark_rating_dict = {}
		bookmark_rating_dict["label"] = "Rating"
		bookmark_rating_dict["values"] = [{"label": "1", "filter_val": "rating_gte$1"},
		{"label": "2", "filter_val": "rating_gte$2"}, 
		{"label": "3", "filter_val": "rating_gte$3"}, 
		{"label": "4", "filter_val": "rating_gte$4"},
		{"label": "5", "filter_val": "rating_gte$5"}]
		result_json.append(bookmark_rating_dict)

		return result_json

class PostgresServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, **_ignored):
        if not self._instance:
            self._instance = PostgresProvider()
        return self._instance


factory = object_factory.ObjectFactory()
factory.register_builder('ELASTICSEARCH', ElasticSearchServiceBuilder())
factory.register_builder('POSTGRES', PostgresServiceBuilder())
factory.register_builder('Default', PostgresServiceBuilder())