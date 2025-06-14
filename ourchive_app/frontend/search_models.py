class ParentSearch():
	def __init__(self, work_search, bookmark_search, collection_search, user_search, tag_search, order_by, search_name):
		self.work_search = work_search
		self.bookmark_search = bookmark_search
		self.collection_search = collection_search
		self.user_search = user_search
		self.tag_search = tag_search
		self.options = {'split_include_exclude': False, 'order_by': order_by}
		self.tag_id = None
		self.attr_id = None
		self.work_type_id = None
		if search_name:
			self.search_name = search_name

	def get_dict(self):
		self.work_search = self.work_search.__dict__
		self.bookmark_search = self.bookmark_search.__dict__
		self.collection_search = self.collection_search.__dict__
		self.user_search = self.user_search.__dict__
		self.tag_search = self.tag_search.__dict__
		return self.__dict__


class ObjectSearch():
	def __init__(self, term, include_filter=None, exclude_filter=None):
		self.term = term
		self.page = 1
		self.include_filter = {'tags': [], 'attributes': []} if not include_filter else include_filter
		self.exclude_filter = {'tags': [], 'attributes': []} if not exclude_filter else exclude_filter


class TagSearch(ObjectSearch):
	def __init__(self, term):
		super(TagSearch, self).__init__(term, {'tag_type': [], 'text': []}, {'tag_type': [], 'text': []})


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
	def with_term(self, term, pagination=None, order_by='-updated_on', search_name=None):
		work_search = ObjectSearch(term)
		bookmark_search = ObjectSearch(term)
		collection_search = ObjectSearch(term)
		user_search = ObjectSearch(term)
		tag_search = TagSearch(term)
		return_obj = ParentSearch(work_search, bookmark_search, collection_search, user_search, tag_search, order_by, search_name)

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
		return return_obj

	def get_object_type(self, filter_term):
		if 'audio' in filter_term:
			return 'work'
		elif 'tag' in filter_term:
			return 'tag'
		elif 'attribute' in filter_term:
			return 'attribute'
		elif 'work' in filter_term:
			return 'work'
		elif 'complete' in filter_term:
			return 'work'
		elif 'rating' in filter_term:
			return 'bookmark'
		elif 'chive' in filter_term:
			return 'chive'


class ReturnKeys(object):
	def __init__(self):
		self.include = []
		self.exclude = []

	def add_val(self, include_exclude, val):
		if include_exclude == 'include':
			self.include.append(val)
		if include_exclude == 'exclude':
			self.exclude.append(val)


class SearchRequest(object):
	def __init__(self, post_data, return_keys):
		self.post_data = post_data
		self.return_keys = return_keys
