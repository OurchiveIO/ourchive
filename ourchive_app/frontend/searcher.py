from django.conf import settings
from .search_models import SearchObject, ReturnKeys, SearchRequest
from .view_utils import *
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

# values we don't want to send to the API
NONFILTER_VALS = ['csrfmiddlewaretoken', 'term', 'order_by', 'search-name', 'search_id']
# values we don't want to add to the frontend facets
NONRETAIN_VALS = ['order_by', 'active_tab', 'work_type']


def get_default_search_result_tab(resultsets):
	most_results = 0
	default_tab = ''
	for results in resultsets:
		if results[0] > most_results:
			most_results = results[0]
			default_tab = results[1]
	return default_tab


def add_filter_to_work(filter_val, filter_details, work_filter):
	if not filter_val:
		filter_key = filter_details[0]
		filter_val = filter_details[1]
	else:
		filter_key = filter_details[1]
	if filter_key in work_filter and len(work_filter[filter_key]) > 0:
		work_filter[filter_key].append(filter_val)
	else:
		work_filter[filter_key] = []
		work_filter[filter_key].append(filter_val)
	return work_filter


def add_filter_to_collection(filter_val, filter_details, collection_filter):
	if not filter_val:
		filter_key = filter_details[0]
		filter_val = filter_details[1]
	else:
		filter_key = filter_details[1]
	if filter_key in collection_filter and len(collection_filter[filter_key]) > 0:
		collection_filter[filter_key].append(filter_val)
	else:
		collection_filter[filter_key] = []
		collection_filter[filter_key].append(filter_val)
	return collection_filter


def add_filter_to_tag(filter_val, filter_details, tag_filter, work_filter, bookmark_filter, collection_filter):
	tag_type = filter_details[0]
	tag_text = filter_val if filter_val else ''
	tag_filter['tag_type'].append(tag_type)
	tag_filter['text'].append(tag_text)
	work_filter['tags'].append(tag_text)
	bookmark_filter['tags'].append(tag_text)
	collection_filter['tags'].append(tag_text)
	return [tag_filter, work_filter, bookmark_filter, collection_filter]


def add_filter_to_attribute(filter_val, work_filter, bookmark_filter, collection_filter):
	attribute_text = filter_val if filter_val else ''
	work_filter['attributes'].append(attribute_text)
	bookmark_filter['attributes'].append(attribute_text)
	collection_filter['attributes'].append(attribute_text)
	return [work_filter, bookmark_filter, collection_filter]


def add_filter_to_bookmark(filter_val, filter_details, bookmark_filter):
	filter_key = filter_details[2] if len(filter_details) > 2 else filter_details[0]
	if filter_details[0] in bookmark_filter and len(bookmark_filter[filter_key]) > 0:
		bookmark_filter[filter_key].append(filter_val)
	else:
		bookmark_filter[filter_key] = []
		bookmark_filter[filter_key].append(filter_val)
	return bookmark_filter


def build_request_filters(request, include_exclude, request_object, request_builder, key, filter_val):
	# TODO: split this into two methods, include and exclude. refactor first with include, then split.
	filter_details = key.split(',')
	if len(filter_details) == 1:
		if not filter_val:
			return request_object
	filter_key = filter_details[2] if len(filter_details) > 2 else filter_details[1]
	filter_type = request_builder.get_object_type(filter_key)
	if filter_type == 'attribute':
		filter_val = filter_details[1]
	if filter_type == 'work':
		if include_exclude == 'include':
			request_object.work_search.include_filter = add_filter_to_work(filter_val, filter_details, request_object.work_search.include_filter)
		else:
			request_object.work_search.exclude_filter = add_filter_to_work(filter_val, filter_details, request_object.work_search.exclude_filter)
	elif filter_type == 'tag':
		if include_exclude == 'include':
			updated_filters = add_filter_to_tag(
				filter_val,
				filter_details,
				request_object.tag_search.include_filter,
				request_object.work_search.include_filter,
				request_object.bookmark_search.include_filter,
				request_object.collection_search.include_filter)
			request_object.tag_search.include_filter = updated_filters[0]
			request_object.work_search.include_filter = updated_filters[1]
			request_object.bookmark_search.include_filter = updated_filters[2]
			request_object.collection_search.include_filter = updated_filters[3]
		else:
			updated_filters = add_filter_to_tag(
				filter_val,
				filter_details,
				request_object.tag_search.exclude_filter,
				request_object.work_search.exclude_filter,
				request_object.bookmark_search.exclude_filter,
				request_object.collection_search.exclude_filter)
			request_object.tag_search.exclude_filter = updated_filters[0]
			request_object.work_search.exclude_filter = updated_filters[1]
			request_object.bookmark_search.exclude_filter = updated_filters[2]
			request_object.collection_search.exclude_filter = updated_filters[3]
	elif filter_type == 'attribute':
		if include_exclude == 'include':
			updated_filters = add_filter_to_attribute(
				filter_val,
				request_object.work_search.include_filter,
				request_object.bookmark_search.include_filter,
				request_object.collection_search.include_filter)
			request_object.work_search.include_filter = updated_filters[0]
			request_object.bookmark_search.include_filter = updated_filters[1]
			request_object.collection_search.include_filter = updated_filters[2]
		else:
			updated_filters = add_filter_to_attribute(
				filter_val,
				request_object.work_search.exclude_filter,
				request_object.bookmark_search.exclude_filter,
				request_object.collection_search.exclude_filter)
			request_object.work_search.exclude_filter = updated_filters[0]
			request_object.bookmark_search.exclude_filter = updated_filters[1]
			request_object.collection_search.exclude_filter = updated_filters[2]
	elif filter_type == 'bookmark':
		if include_exclude == 'include':
			request_object.bookmark_search.include_filter = add_filter_to_bookmark(filter_val, filter_details, request_object.bookmark_search.include_filter)
		else:
			request_object.bookmark_search.exclude_filter = add_filter_to_bookmark(filter_val, filter_details, request_object.bookmark_search.exclude_filter)
	elif filter_type == "chive":
		if include_exclude == 'include':
			request_object.bookmark_search.include_filter = add_filter_to_bookmark(filter_val, filter_details, request_object.bookmark_search.include_filter)
			request_object.work_search.include_filter = add_filter_to_work(filter_val, filter_details, request_object.work_search.include_filter)
			request_object.collection_search.include_filter = add_filter_to_collection(filter_val, filter_details, request_object.collection_search.include_filter)
		else:
			request_object.bookmark_search.exclude_filter = add_filter_to_bookmark(filter_val, filter_details, request_object.bookmark_search.exclude_filter)
			request_object.work_search.exclude_filter = add_filter_to_work(filter_val, filter_details, request_object.work_search.exclude_filter)
			request_object.collection_search.include_filter = add_filter_to_collection(filter_val, filter_details, request_object.collection_search.include_filter)
	return request_object


def get_empty_response_obj():
	return {'data': []}


def get_search_request(request, request_object, request_builder):
	return_keys = ReturnKeys()
	request_data = request.POST.copy()
	for key in request_data:
		if key == 'tag_id' or key == 'attr_id' or key == 'work_type_id':
			continue
		if key.endswith('tag[]'):
			tag_facets = [x for x in request_data.getlist(key)]
			for facet in tag_facets:
				include_exclude = 'exclude' if 'exclude_' in key else 'include'
				key = key.replace('exclude_', '') if include_exclude == 'exclude' else key.replace('include_', '')
				if key in NONFILTER_VALS or key in NONRETAIN_VALS:
					continue
				else:
					if ',' in key and not facet and not key.endswith(',input'):
						return_keys.add_val(include_exclude, key)
					elif facet:
						key = key.replace(',input', '')
						return_keys.add_val(include_exclude, f'{key},{facet}')
				request_object = build_request_filters(request, include_exclude, request_object, request_builder, key, facet)
		else:
			filter_val = request_data.get(key, None) if request_data.get(key, None) != 'on' else None
			# TODO: YOU NEED TO GET ALL TAGS FROM THEIR LIST VALUES!!!
			include_exclude = 'exclude' if 'exclude_' in key else 'include'
			key = key.replace('exclude_', '') if include_exclude == 'exclude' else key.replace('include_', '')
			if key in NONFILTER_VALS or key in NONRETAIN_VALS:
				continue
			else:
				if ',' in key and not filter_val and not key.endswith(',input'):
					return_keys.add_val(include_exclude, key)
				elif filter_val:
					key = key.replace(',input', '')
					return_keys.add_val(include_exclude, f'{key},{filter_val}')
			request_object = build_request_filters(request, include_exclude, request_object, request_builder, key, filter_val)
	return SearchRequest(request_object, return_keys)


def get_chive_results(response_obj):
	response_obj['data'] = get_object_tags(response_obj['data'])
	response_obj['data'] = get_array_attributes_for_display(response_obj['data'], 'attributes')
	response_obj['data'] = format_date_for_template(response_obj['data'], 'updated_on', True)
	response_obj['pagination_array'] = get_pagination_array(response_obj['pages'])
	return response_obj


def get_tag_results(response_obj):
	response_obj['data'] = group_tags(response_obj['data'])
	response_obj['pagination_array'] = get_pagination_array(response_obj['pages'])
	return response_obj


def build_search(request):
	# prepare search & preserve request data
	tag_id = None
	attr_id = None
	work_type_id = None
	valid_search = False
	search_name = request.POST.get('search-name', None)
	term = ''
	if 'term' in request.GET:
		term = request.GET['term']
		valid_search = True
	elif 'term' in request.POST:
		term = request.POST['term']
		valid_search = True
	if 'tag_id' in request.GET:
		tag_id = request.GET['tag_id']
		term = ""
		valid_search = True
	elif 'attr_id' in request.GET:
		attr_id = request.GET['attr_id']
		term = ""
		valid_search = True
	elif 'work_type' in request.GET:
		work_type_id = request.GET['work_type']
		term = ""
		valid_search = True
	if not valid_search:
		logger.info(f'Not a valid search. Returning. Request get: {request.GET} Request post: {request.POST}')
		return None
	order_by = request.POST['order_by'] if 'order_by' in request.POST else '-updated_on'
	request_builder = SearchObject()
	pagination = {'page': request.GET.get('page', 1), 'obj': request.GET.get('object_type', '')}
	request_object = request_builder.with_term(
		term, pagination, order_by, search_name)
	if tag_id:
		request_object.tag_id = tag_id
	if attr_id:
		request_object.attr_id = attr_id
	if work_type_id:
		request_object.work_type_id = work_type_id
	request_object = get_search_request(request, request_object, request_builder)
	post_request = request_object.post_data.get_dict()
	return post_request


def execute_search(request, post_request):
	active_tab = request.POST.get('active_tab', None)
	if not active_tab:
		object_type = request.GET.get('object_type', '')
		if object_type == 'BookmarkCollection':
			active_tab = 2
		elif object_type == 'Work':
			active_tab = 0
		elif object_type == 'Tag':
			active_tab = 3
		elif object_type == 'Bookmark':
			active_tab = 1
	term = request.POST.get('term', '')
	if not term:
		term = request.GET.get('term')
	tag_id = request.GET.get('tag_id', None)
	attr_id = request.GET.get('attr_id', None)
	work_type_id = request.GET.get('work_type_id', None)
	# make request
	logger.debug(f'Search request data: {post_request}')
	response_json = do_post(f'api/search/', request, data=post_request).response_data
	logger.debug(f'Search response data: {response_json}')
	# process results
	works = get_chive_results(response_json['results']['work']) if 'results' in response_json and 'work' in \
																   response_json[
																	   'results'] else get_empty_response_obj()
	bookmarks = get_chive_results(response_json['results']['bookmark']) if 'results' in response_json and 'bookmark' in \
																		   response_json[
																			   'results'] else get_empty_response_obj()
	tags = get_tag_results(response_json['results']['tag']) if 'results' in response_json and 'tag' in response_json[
		'results'] else get_empty_response_obj()
	users = response_json['results']['user'] if 'results' in response_json and 'user' in response_json[
		'results'] else get_empty_response_obj()
	collections = get_chive_results(
		response_json['results']['collection']) if 'results' in response_json and 'collection' in response_json[
		'results'] else get_empty_response_obj()
	facets = response_json['results']['facets'] if 'results' in response_json and 'facets' in response_json[
		'results'] else [{}, {}]
	works_count = works['page']['count'] if 'page' in works else 0
	bookmarks_count = bookmarks['page']['count'] if 'page' in bookmarks else 0
	collections_count = collections['page']['count'] if 'page' in collections else 0
	tag_count = tags['page']['count'] if 'page' in tags else 0
	search_name = response_json.get('results', {}).get('options', {}).get('search_name', '')
	if not search_name:
		search_name = request.POST.get('search-name', '')
	default_tab = get_default_search_result_tab(
		[
			[works_count, 0],
			[bookmarks_count, 1],
			[collections_count, 2],
			[tag_count, 3],
			[len(users['data']), 4]
		]) if not active_tab else int(active_tab)
	order_by = response_json.get('results', {}).get('options', {}).get('order_by', '-updated_on')
	template_data = {
		'works': works,
		'bookmarks': bookmarks,
		'tags': tags,
		'users': users,
		'tag_count': tag_count,
		'collections': collections,
		'facets': facets,
		'default_tab': default_tab,
		'click_func': 'getFormVals(event)',
		'root': settings.ROOT_URL,
		'term': term,
		'order_by': order_by,
		'search_name': search_name
	}
	if tag_id:
		template_data['tag_id'] = tag_id
	if attr_id:
		template_data['attr_id'] = attr_id
	if work_type_id:
		template_data['work_type_id'] = work_type_id
	return template_data


def build_and_execute_search(request):
	post_request = build_search(request)
	if not post_request:
		return None
	return execute_search(request, post_request)
