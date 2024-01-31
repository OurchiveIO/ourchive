from django.conf import settings
from .search_models import SearchObject
from .view_utils import *

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


def build_request_filters(request, include_exclude, request_object, request_builder, key, filter_val):
	filter_key = f'{include_exclude}_filter'
	filter_options = key.split('|')
	if 'ranges' in key:
		if filter_options[0] not in request_object['work_search'][filter_key]:
			request_object['work_search'][filter_key][filter_options[0]] = [([filter_options[3], filter_options[2]])]
		else:
			request_object['work_search'][filter_key][filter_options[0]].append((filter_options[3], filter_options[2]))
	else:
		# TODO: refactor: request object should stay a true object, __dict__ should be called
		# on making the API request, and collections.defaultdict should be used to prevent cluttered logic
		for option in filter_options:
			filter_details = option.split('$')
			filter_type = request_builder.get_object_type(filter_details[0])
			if len(filter_details) == 1:
				if not filter_val:
					continue
			else:
				filter_val = filter_details[1]
			if filter_type == 'work':
				if filter_details[0] in request_object['work_search'][filter_key] and len(request_object['work_search'][filter_key][filter_details[0]]) > 0:
					request_object['work_search'][filter_key][filter_details[0]].append(filter_val)
				else:
					request_object['work_search'][filter_key][filter_details[0]] = []
					request_object['work_search'][filter_key][filter_details[0]].append(filter_val)
			elif filter_type == 'tag':
				tag_type = filter_details[0].split(',')[1]
				tag_text = (filter_val.split(',')[1]).lower() if filter_val.split(',')[1] else ''
				request_object['tag_search'][filter_key]['tag_type'].append(tag_type)
				request_object['tag_search'][filter_key]['text'].append(tag_text)
				request_object['work_search'][filter_key]['tags'].append(tag_text)
				request_object['bookmark_search'][filter_key]['tags'].append(tag_text)
			elif filter_type == 'attribute':
				attribute_text = (filter_val.split(',')[1]).lower() if filter_val.split(',')[1] else ''
				request_object['work_search'][filter_key]['attributes'].append(attribute_text)
				request_object['bookmark_search'][filter_key]['attributes'].append(attribute_text)
				request_object['collection_search'][filter_key]['attributes'].append(attribute_text)
			elif filter_type == 'bookmark':
				if filter_details[0] in request_object['bookmark_search'][filter_key] and len(request_object['bookmark_search'][filter_key][filter_details[0]]) > 0:
					request_object['bookmark_search'][filter_key][filter_details[0]].append(filter_val)
				else:
					request_object['bookmark_search'][filter_key][filter_details[0]] = []
					request_object['bookmark_search'][filter_key][filter_details[0]].append(filter_val)
	return request_object


def add_facet_to_filters(facets, label, value, item, excluded=True):
	if label in NONRETAIN_VALS:
		return facets
	facet_added = False
	for facet in facets:
		if facet['label'] == label:
			for val in facet['values']:
				if val['label'] == value:
					facet_added = True
					break
			if not facet_added:
				facet['values'].append({'label': value, 'filter_val': item})
			facet_added = True
			break
		elif label in facet.get('filters', []):
			key_field = 'include_value' if not excluded else 'exclude_value'
			for val in facet['values']:
				if val['filter_val'] == label:
					val[key_field] = value
					facet_added = True
					break
	if not facet_added:
		facets.append({'label': label, 'excluded': excluded, 'values': [{'label': value, 'filter_val': item}]})
	return facets


def iterate_facets(facets, item, excluded=True):
	if item == 'any_all':
		return facets
	if '$' in item and ',' in item:
		split = item.split('$')
		label_split = split[0].split(',')
		val_split = split[1].split(',')
		facets = add_facet_to_filters(facets, label_split[1], val_split[1], item, excluded)
	elif '$' in item:
		# assumes text format e.g. word count: word_count_gte$20000
		split = item.split('$')
		facets = add_facet_to_filters(facets, split[0], split[1], split[0], excluded)
	return facets


def get_response_facets(response_json, request_object):
	facets = response_json['results']['facet']
	print(request_object[1]['exclude'])
	for item in request_object[1]['exclude']:
		facets = iterate_facets(facets, item)
	for item in request_object[1]['include']:
		facets = iterate_facets(facets, item, False)
	return facets


def get_empty_response_obj():
	return {'data': []}


def get_search_request(request, request_object, request_builder):
	return_keys = {'include': [], 'exclude': []}
	for key in request.POST:
		filter_val = request.POST.get(key, None)
		include_exclude = 'exclude' if 'exclude_' in key else 'include'
		key = key.replace('exclude_', '') if include_exclude == 'exclude' else key.replace('include_', '')
		if key in NONFILTER_VALS:
			continue
		else:
			if '$' in key:
				return_keys[include_exclude].append(key)
			elif filter_val:
				return_keys[include_exclude].append(f'{key}${filter_val}')
		request_object = build_request_filters(request, include_exclude, request_object, request_builder, key, filter_val)
	return [request_object, return_keys]


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
	if 'term' in request.GET:
		term = request.GET['term']
	elif 'term' in request.POST:
		term = request.POST['term']
	elif 'tag_id' in request.GET:
		tag_id = request.GET['tag_id']
		term = ""
	elif 'attr_id' in request.GET:
		attr_id = request.GET['attr_id']
		term = ""
	else:
		return None
	active_tab = request.POST.get('active_tab', None)
	include_filter_any = 'any' if request.POST.get('include_any_all') == 'on' else 'all'
	exclude_filter_any = 'any' if request.POST.get('exclude_any_all') == 'on' else 'all'
	order_by = request.POST['order_by'] if 'order_by' in request.POST else '-updated_on'
	request_builder = SearchObject()
	pagination = {'page': request.GET.get('page', 1), 'obj': request.GET.get('object_type', '')}
	request_object = request_builder.with_term(term, pagination, (include_filter_any, exclude_filter_any), order_by)
	if tag_id:
		request_object["tag_id"] = tag_id
	if attr_id:
		request_object["attr_id"] = attr_id
	request_object = get_search_request(request, request_object, request_builder)
	# make request
	response_json = do_post(f'api/search/', request, data=request_object[0]).response_data
	# process results
	works = get_chive_results(response_json['results']['work']) if 'work' in response_json['results'] else get_empty_response_obj()
	bookmarks = get_chive_results(response_json['results']['bookmark']) if 'bookmark' in response_json['results'] else get_empty_response_obj()
	tags = get_tag_results(response_json['results']['tag']) if 'tag' in response_json['results'] else get_empty_response_obj()
	users = response_json['results']['user'] if 'user' in response_json['results'] else get_empty_response_obj()
	collections = get_chive_results(response_json['results']['collection']) if 'collection' in response_json['results'] else get_empty_response_obj()
	facets = get_response_facets(response_json, request_object) if 'facet' in response_json['results'] else {}
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
		'facets': facets,
		'default_tab': default_tab,
		'click_func': 'getFormVals(event)',
		'root': settings.ROOT_URL, 'term': term,
		'keys_include': request_object[1]['include'],
		'keys_exclude': request_object[1]['exclude']
	}
	if tag_id:
		template_data['tag_id'] = tag_id
	return template_data
