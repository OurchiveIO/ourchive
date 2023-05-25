from . import search
from django.conf import settings
from api.models import OurchiveSetting

class OurchiveSearch:
	def __init__(self):
		config = {}
		search_backend = OurchiveSetting.objects.filter(name='Search Provider').first().value
		self.searcher = search.factory.create(search_backend, **config)

	def do_search(self, **kwargs):
		results = {}
		if ('work_search') in kwargs:
			results['work'] = self.searcher.search_works(**kwargs['work_search'])
		if ('bookmark_search') in kwargs:
			results['bookmark'] = self.searcher.search_bookmarks(**kwargs['bookmark_search'])
		if ('tag_search') in kwargs:
			results['tag'] = self.searcher.search_tags(**kwargs['tag_search'])
		if ('user_search') in kwargs:
			results['user'] = self.searcher.search_users(**kwargs['user_search'])
		results['facet'] = self.searcher.get_result_facets(results)
		return results

