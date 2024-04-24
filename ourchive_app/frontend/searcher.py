from django.conf import settings
from .search_models import SearchObject, SearchRequest
from .view_utils import *
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

# values we don't want to send to the API
NONFILTER_VALS = ['csrfmiddlewaretoken', 'term']
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


def add_filter_to_tag(filter_val, filter_details, tag_filter, work_filter, bookmark_filter):
	tag_type = filter_details[0]
	tag_text = filter_val.lower() if filter_val else ''
	tag_filter['tag_type'].append(tag_type)
	tag_filter['text'].append(tag_text)
	work_filter['tags'].append(tag_text)
	bookmark_filter['tags'].append(tag_text)
	return [tag_filter, work_filter, bookmark_filter]


def add_filter_to_attribute(filter_val, work_filter, bookmark_filter, collection_filter):
	attribute_text = filter_val
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
	# TODO: refactor: request object should stay a true object, __dict__ should be called
	# on making the API request, and collections.defaultdict should be used to prevent cluttered logic
	filter_key = filter_details[2] if len(filter_details) > 2 else filter_details[0]
	filter_type = request_builder.get_object_type(filter_key)
	if len(filter_details) == 1:
		if not filter_val:
			return request_object
	elif filter_type == 'tag' or filter_type == 'attribute':
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
				request_object.bookmark_search.include_filter)
			request_object.tag_search.include_filter = updated_filters[0]
			request_object.work_search.include_filter = updated_filters[1]
			request_object.bookmark_search.include_filter = updated_filters[2]
		else:
			updated_filters = add_filter_to_tag(
				filter_val,
				filter_details,
				request_object.tag_search.exclude_filter,
				request_object.work_search.exclude_filter,
				request_object.bookmark_search.exclude_filter)
			request_object.tag_search.exclude_filter = updated_filters[0]
			request_object.work_search.exclude_filter = updated_filters[1]
			request_object.bookmark_search.exclude_filter = updated_filters[2]
	elif filter_type == 'attribute':
		# TODO: validate & test
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
		# TODO: validate & test
		if include_exclude == 'include':
			request_object.bookmark_search.include_filter = add_filter_to_bookmark(filter_val, filter_details, request_object.bookmark_search.include_filter)
		else:
			request_object.bookmark_search.exclude_filter = add_filter_to_bookmark(filter_val, filter_details, request_object.bookmark_search.exclude_filter)
	return request_object


def get_empty_response_obj():
	return {'data': []}


def get_search_request(request, request_object, request_builder):
	for key in request.POST:
		if key == 'tag_id' or key == 'attr_id':
			continue
		filter_val = request.POST.get(key, None) if request.POST.get(key, None) != 'on' else None
		include_exclude = 'exclude' if 'exclude_' in key else 'include'
		key = key.replace('exclude_', '') if include_exclude == 'exclude' else key.replace('include_', '')
		if key in NONFILTER_VALS:
			continue
		request_object = build_request_filters(request, include_exclude, request_object, request_builder, key, filter_val)
	return SearchRequest(request_object)


def get_chive_results(response_obj):
	response_obj['data'] = get_object_tags(response_obj['data'])
	response_obj['data'] = get_array_attributes_for_display(response_obj['data'], 'attributes')
	response_obj['data'] = format_date_for_template(response_obj['data'], 'updated_on', True)
	return response_obj


def get_tag_results(response_obj):
	response_obj['data'] = group_tags(response_obj['data'])
	return response_obj


def build_and_execute_search(request):
	# prepare search & preserve request data
	tag_id = None
	attr_id = None
	valid_search = False
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
	if not valid_search:
		logger.info(f'Not a valid search. Returning. Request get: {request.GET} Request post: {request.POST}')
		return None
	active_tab = request.POST.get('active_tab', None)
	include_filter_any = 'any' if request.POST.get('include_any_all') == 'on' else 'all'
	exclude_filter_any = 'any' if request.POST.get('exclude_any_all') == 'on' else 'all'
	order_by = request.POST['order_by'] if 'order_by' in request.POST else '-updated_on'
	request_builder = SearchObject()
	pagination = {'page': request.GET.get('page', 1), 'obj': request.GET.get('object_type', '')}
	request_object = request_builder.with_term(term, pagination, (include_filter_any, exclude_filter_any), order_by)
	if tag_id:
		request_object.tag_id = tag_id
	if attr_id:
		request_object.attr_id = attr_id
	request_object = get_search_request(request, request_object, request_builder)
	post_request = request_object.post_data.get_dict()
	# make request
	logger.debug(f'Search request data: {post_request}')
	response_json = do_post(f'api/search/', request, data=post_request).response_data
	logger.debug(f'Search response data: {response_json}')
	# process results
	works = get_chive_results(response_json['results']['work']) if 'results' in response_json and 'work' in response_json['results'] else get_empty_response_obj()
	bookmarks = get_chive_results(response_json['results']['bookmark']) if 'results' in response_json and 'bookmark' in response_json['results'] else get_empty_response_obj()
	tags = get_tag_results(response_json['results']['tag']) if 'results' in response_json and 'tag' in response_json['results'] else get_empty_response_obj()
	users = response_json['results']['user'] if 'results' in response_json and 'user' in response_json['results'] else get_empty_response_obj()
	collections = get_chive_results(response_json['results']['collection']) if 'results' in response_json and 'collection' in response_json['results'] else get_empty_response_obj()
	include_facets = response_json['results'].get('include_facets', [])
	exclude_facets = response_json['results'].get('exclude_facets', [])
	include_mode = response_json['results'].get('include_mode', 'all')
	exclude_mode = response_json['results'].get('exclude_mode', 'all')
	works_count = works['page']['count'] if 'page' in works else 0
	bookmarks_count = bookmarks['page']['count'] if 'page' in bookmarks else 0
	collections_count = collections['page']['count'] if 'page' in collections else 0
	tag_count = tags['page']['count'] if 'page' in tags else 0
	default_tab = get_default_search_result_tab(
		[
			[works_count, 0],
			[bookmarks_count, 1],
			[collections_count, 2],
			[tag_count, 3],
			[len(users['data']), 4]
		]) if not active_tab else active_tab
	template_data = {
		'works': works,
		'bookmarks': bookmarks,
		'tags': tags,
		'users': users,
		'tag_count': tag_count,
		'collections': collections,
		'include_facets': include_facets,
		'exclude_facets': exclude_facets,
		'default_tab': default_tab,
		'click_func': 'getFormVals(event)',
		'root': settings.ROOT_URL, 'term': term,
		'include_mode': include_mode,
		'exclude_mode': exclude_mode
	}
	if tag_id:
		template_data['tag_id'] = tag_id
	return template_data
