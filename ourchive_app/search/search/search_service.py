from . import search
from core.models import OurchiveSetting
from search.search.search_results import SearchResults


class OurchiveSearch:
	def __init__(self):
		config = {}
		search_backend = OurchiveSetting.objects.filter(name='Search Provider').first().value
		self.searcher = search.factory.create(search_backend, **config)
		self.result_builder = SearchResults()

	def do_search(self, user_id, **kwargs):
		results = {}
		tags = []
		if 'tag_id' in kwargs and kwargs['tag_id']:
			return self.filter_by_tag(**kwargs)
		if 'attr_id' in kwargs and kwargs['attr_id']:
			return self.filter_by_attribute(**kwargs)
		if 'work_type_id' in kwargs and kwargs['work_type_id']:
			return self.filter_by_work_type(**kwargs)
		if ('work_search') in kwargs:
			results['work'] = self.searcher.search_works(kwargs['options'], **kwargs['work_search'])
			tags = tags + results['work'].pop('tags')
		if ('bookmark_search') in kwargs:
			results['bookmark'] = self.searcher.search_bookmarks(kwargs['options'], **kwargs['bookmark_search'])
			tags = tags + results['bookmark'].pop('tags')
		if ('tag_search') in kwargs:
			results['tag'] = self.searcher.search_tags(kwargs['options'], **kwargs['tag_search'])
			tags = tags + results['tag'].pop('tags')
		if ('user_search') in kwargs:
			results['user'] = self.searcher.search_users(kwargs['options'], **kwargs['user_search'])
			tags = tags + results['user'].pop('tags')
		if ('collection_search') in kwargs:
			results['collection'] = self.searcher.search_collections(kwargs['options'], **kwargs['collection_search'])
			tags = tags + results['collection'].pop('tags')
		kwargs['user_id'] = user_id
		facets = self.result_builder.get_result_facets(results, kwargs, tags)
		results['facets'] = facets['include_facets']
		results['options'] = facets['options']
		return results

	def filter_by_work_type(self, **kwargs):
		if not kwargs['work_type_id'].isdigit():
			return {'results': {'errors': ['Work type id must be a number.']}}
		results = self.searcher.filter_by_work_type(**kwargs)
		facets = self.result_builder.get_result_facets(results, kwargs)
		results['facets'] = facets['include_facets']
		results['options'] = facets['options']
		return results

	def filter_by_tag(self, **kwargs):
		if not kwargs['tag_id'].isdigit():
			return {'results': {'errors': ['Tag id must be a number.']}}
		results = self.searcher.filter_by_tag(**kwargs)
		facets = self.result_builder.get_result_facets(results, kwargs)
		results['facets'] = facets['include_facets']
		results['options'] = facets['options']
		return results

	def filter_by_attribute(self, **kwargs):
		if not kwargs['attr_id'].isdigit():
			return {'results': {'errors': ['Attribute id must be a number.']}}
		results = self.searcher.filter_by_attribute(**kwargs)
		facets = self.result_builder.get_result_facets(results, kwargs)
		results['facets'] = facets['include_facets']
		results['options'] = facets['options']
		return results

	def do_tag_search(self, term, tag_type, fetch_all):
		results = {}
		if term is not None:
			results = self.searcher.autocomplete_tags(term, tag_type, fetch_all)
		return results

	def do_work_search(self, term, user):
		results = {}
		if term is not None:
			results = self.searcher.autocomplete_works(term, user)
		return results

	def do_user_search(self, term, user):
		results = {}
		if term is not None:
			results = self.searcher.autocomplete_users(term, user)
		return results

	def do_series_search(self, term, user):
		results = {}
		if term is not None:
			results = self.searcher.autocomplete_series(term, user)
		return results

	def do_anthology_search(self, term, user):
		results = {}
		if term is not None:
			results = self.searcher.autocomplete_anthologies(term, user)
		return results
