class ParentSearch():
	def __init__(self, work_search, bookmark_search, collection_search, user_search, tag_search):
		self.work_search = work_search
		self.bookmark_search = bookmark_search
		self.collection_search = collection_search
		self.user_search = user_search
		self.tag_search = tag_search

	def get_dict(self):
		self.work_search = self.work_search.__dict__
		self.bookmark_search = self.bookmark_search.__dict__
		self.collection_search = self.collection_search.__dict__
		self.user_search = self.user_search.__dict__
		self.tag_search = self.tag_search.__dict__
		return self.__dict__


class ObjectSearch():
	def __init__(self, mode, order_by, term, include_filter=None, exclude_filter=None):
		self.term = term
		self.include_mode = mode[0]
		self.exclude_mode = mode[1]
		self.page = 1
		self.order_by = order_by
		self.include_filter = {'tags': [], 'attributes': []} if not include_filter else include_filter
		self.exclude_filter = {'tags': [], 'attributes': []} if not exclude_filter else exclude_filter


class TagSearch(ObjectSearch):
	def __init__(self, mode, order_by, term):
		super(TagSearch, self).__init__(mode, order_by, term, {'tag_type': [], 'text': []}, {'tag_type': [], 'text': []})


class WorkSearch(object):
	def from_json(self, json_obj):
		self.id = json_obj["id"]
		self.title = json_obj["title"]
		self.summary = json_obj["summary"]
		self.notes = None if json_obj["notes"] == "null" else json_obj["notes"]
		self.is_complete = self.convert_bool(json_obj["is_complete"])
		self.process_status = None if json_obj["process_status"] == "null" else json_obj["process_status"]
		self.cover_url = None if json_obj["cover_url"] == "null" else json_obj["cover_url"]
		self.cover_alt_text = None if json_obj["cover_alt_text"] == "null" else json_obj["cover_alt_text"]
		self.epub_id = None if json_obj["epub_id"] == "null" else json_obj["epub_id"]
		self.zip_id = None if json_obj["zip_id"] == "null" else json_obj["zip_id"]
		self.anon_comments_permitted = self.convert_bool(json_obj["anon_comments_permitted"])
		self.comments_permitted = self.convert_bool(json_obj["comments_permitted"])
		self.word_count = json_obj["word_count"]
		self.audio_length = json_obj["audio_length"]
		self.user_id = json_obj["user_id"]
		self.work_type = None if json_obj["work_type"] == "null" else json_obj["work_type"]
		self.user = json_obj["user"]

	def convert_bool(string_bool):
		return False if string_bool == "false" else True


class SearchObject(object):
	def with_term(self, term, pagination=None, mode=('all', 'all'), order_by='-updated_on'):
		work_search = ObjectSearch(mode, order_by, term)
		bookmark_search = ObjectSearch(mode, order_by, term)
		collection_search = ObjectSearch(mode, order_by, term)
		user_search = ObjectSearch(mode, order_by, term)
		tag_search = TagSearch(mode, order_by, term)
		return_obj = ParentSearch(work_search, bookmark_search, collection_search, user_search, tag_search)

		if pagination:
			obj = pagination['obj'].lower()
			if obj == 'work':
				return_obj.work_search.page = pagination['page']
			elif obj == 'bookmark':
				return_obj.bookmark_search.page = pagination['page']
			elif obj == 'tag':
				return_obj.tag_search.page = pagination['page']
			elif obj == 'bookmarkcollection':
				return_obj.collection_search.page = pagination['page']
		return return_obj.get_dict()

	def get_object_type(self, filter_term):
		if 'audio' in filter_term:
			return 'work'
		elif 'tag_type' in filter_term:
			return 'tag'
		elif 'attribute_type' in filter_term:
			return 'attribute'
		elif 'work_type' in filter_term:
			return 'work'
		elif 'word_count' in filter_term:
			return 'work'
		elif 'complete' in filter_term:
			return 'work'
		elif 'rating' in filter_term:
			return 'bookmark'
