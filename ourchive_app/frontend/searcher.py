from django.conf import settings
from .search_models import SearchObject
from .view_utils import *


def get_default_search_result_tab(resultsets):
	most_results = 0
	default_tab = ''
	for results in resultsets:
		if results[0] > most_results:
			most_results = results[0]
			default_tab = results[1]
	return default_tab


def get_search_request(request, request_object, request_builder):
	return_keys = {'include': [], 'exclude': []}
	for key in request.POST:
		filter_val = request.POST[key]
		include_exclude = 'exclude' if 'exclude_' in key else 'include'
		key = key.replace('exclude_', '') if include_exclude == 'exclude' else key.replace('include_', '')
		if filter_val == 'csrfmiddlewaretoken':
			continue
		else:
			return_keys[include_exclude].append(key)
		if filter_val == 'term':
			continue
		if 'ranges' in key:
			filter_details = key.split('|')
			if filter_details[0] not in request_object['work_search'][f'{include_exclude}_filter']:
				request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]] = [([filter_details[3], filter_details[2]])]
			else:
				request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]].append((filter_details[3], filter_details[2]))
		else:
			# TODO: make this less bad
			filter_options = key.split('|')
			for option in filter_options:
				filter_details = option.split('$')
				filter_type = request_builder.get_object_type(filter_details[0])
				if filter_type == 'work':
					if filter_details[0] in request_object['work_search'][f'{include_exclude}_filter'] and len(request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]]) > 0:
						request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]].append(filter_details[1])
					else:
						request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]] = []
						request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]].append(filter_details[1])
				elif filter_type == 'tag':
					tag_type = filter_details[0].split(',')[1]
					tag_text = (filter_details[1].split(',')[1]).lower() if filter_details[1].split(',')[1] else ''
					request_object['tag_search'][f'{include_exclude}_filter']['tag_type'].append(tag_type)
					request_object['tag_search'][f'{include_exclude}_filter']['text'].append(tag_text)
					request_object['work_search'][f'{include_exclude}_filter']['tags'].append(tag_text)
					request_object['bookmark_search'][f'{include_exclude}_filter']['tags'].append(tag_text)
				elif filter_type == 'attribute':
					attribute_text = (filter_details[1].split(',')[1]).lower() if filter_details[1].split(',')[1] else ''
					request_object['work_search'][f'{include_exclude}_filter']['attributes'].append(attribute_text)
					request_object['bookmark_search'][f'{include_exclude}_filter']['attributes'].append(attribute_text)
					request_object['collection_search'][f'{include_exclude}_filter']['attributes'].append(attribute_text)
				elif filter_type == 'bookmark':
					if filter_details[0] in request_object['bookmark_search'][f'{include_exclude}_filter'] and len(request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]]) > 0:
						request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]].append(filter_details[1])
					else:
						request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]] = []
						request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]].append(filter_details[1])
	return [request_object, return_keys]


def build_and_execute_search(request):
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
	works = {'data': []}
	bookmarks = {'data': []}
	tags = {'data': []}
	users = {'data': []}
	collections = {'data': []}
	facets = {}
	tag_count = 0
	response_json = do_post(f'api/search/', request, data=request_object[0]).response_data
	if 'work' in response_json['results']:
		works = response_json['results']['work']
		works['data'] = get_object_tags(works['data'])
		works['data'] = get_array_attributes_for_display(works['data'], 'attributes')
		works['data'] = format_date_for_template(works['data'], 'updated_on', True)
	if 'bookmark' in response_json['results']:
		bookmarks = response_json['results']['bookmark']
		bookmarks['data'] = get_object_tags(bookmarks['data'])
		bookmarks['data'] = get_array_attributes_for_display(bookmarks['data'], 'attributes')
		bookmarks['data'] = format_date_for_template(bookmarks['data'], 'updated_on', True)
	if 'tag' in response_json['results']:
		tags = response_json['results']['tag']
		tags['data'] = group_tags(tags['data'])
		tag_count = len(response_json['results']['tag']['data'])
	if 'user' in response_json['results']:
		users = response_json['results']['user']
	if 'collection' in response_json['results']:
		collections = response_json['results']['collection']
		collections['data'] = get_object_tags(collections['data'])
		collections['data'] = get_array_attributes_for_display(collections['data'], 'attributes')
		collections['data'] = format_date_for_template(collections['data'], 'updated_on', True)
	if 'facet' in response_json['results']:
		facets = response_json['results']['facet']
		for item in request_object[1]['exclude']:
			if item == 'any_all':
				continue
			facet_added = False
			split = item.split('$')
			label_split = split[0].split(',')
			val_split = split[1].split(',')
			for facet in facets:
				if facet['label'] == label_split[1]:
					for val in facet['values']:
						if val['label'] == val_split[1]:
							facet_added = True
							break
					if not facet_added:
						facet['values'].append({'label': val_split[1], 'filter_val': item})
					facet_added = True
					break
			if not facet_added:
				facets.append({'label': label_split[1], 'excluded': True, 'values': [{'label': val_split[1], 'filter_val': item}]})
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
		])
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
