from . import search
from api.models import OurchiveSetting
import numbers


class OurchiveSearch:
	def __init__(self):
		config = {}
		search_backend = OurchiveSetting.objects.filter(name='Search Provider').first().value
		self.searcher = search.factory.create(search_backend, **config)

	def do_search(self, **kwargs):
		results = {}
		if 'tag_id' in kwargs:
			return self.filter_by_tag(**kwargs)
		if ('work_search') in kwargs:
			results['work'] = self.searcher.search_works(**kwargs['work_search'])
		if ('bookmark_search') in kwargs:
			results['bookmark'] = self.searcher.search_bookmarks(**kwargs['bookmark_search'])
		if ('tag_search') in kwargs:
			results['tag'] = self.searcher.search_tags(**kwargs['tag_search'])
		if ('user_search') in kwargs:
			results['user'] = self.searcher.search_users(**kwargs['user_search'])
		if ('collection_search') in kwargs:
			results['collection'] = self.searcher.search_collections(**kwargs['collection_search'])
		results['facet'] = self.searcher.get_result_facets(results)
		return results

	def filter_by_tag(self, **kwargs):
		if not isinstance(kwargs['tag_id'], numbers.Number):
			return {'results': {'errors': ['Tag id must be a number.']}}
		results = self.searcher.filter_by_tag(**kwargs)
		results['facet'] = self.searcher.get_result_facets(results)
		return results

	def do_tag_search(self, term, tag_type, fetch_all):
		results = {}
		if term is not None:
			results = self.searcher.autocomplete_tags(term, tag_type, fetch_all)
		return results

	def do_bookmark_search(self, term, user):
		results = {}
		if term is not None:
			results = self.searcher.autocomplete_bookmarks(term, user)
		return results
