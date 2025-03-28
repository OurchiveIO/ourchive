from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, logout, login
from django.contrib import messages
from frontend.search_models import SearchObject
from html import escape, unescape
from django.http import HttpResponse, FileResponse
import logging
from frontend.api_utils import do_get, do_post, do_patch, do_delete, validate_captcha
from django.utils.translation import gettext as _
from core import utils
from core.models import TagType
from django.views.decorators.cache import never_cache
from dateutil.parser import *
from dateutil import tz
from urllib.parse import unquote, quote
import random
from django.core.cache import cache
from django.views.decorators.vary import vary_on_cookie
from operator import itemgetter
from datetime import *
from search.search import constants as search_constants
from copy import deepcopy

from search.search.constants import WORK_TYPE_FILTER_KEY

logger = logging.getLogger(__name__)


def group_tags(tags):
	search_groups = {}
	# tag_parent format: {'type_name': [tags]}
	tag_parent = {}
	for tag in tags:
		if tag['tag_type'] not in tag_parent:
			tag_parent[tag['tag_type']] = [tag]
		else:
			tag_parent[tag['tag_type']].append(tag)
	for tag_type in tag_parent.keys():
		search_group = tag_parent[tag_type][0].get('search_group', TagType.DEFAULT_SEARCH_GROUP_LABEL)
		if search_group not in search_groups:
			search_groups[search_group] = {tag_type: tag_parent[tag_type]}
		else:
			if tag_type not in search_groups[search_group]:
				search_groups[search_group][tag_type] = tag_parent[tag_type]
			else:
				search_groups[search_group][tag_type].append(tag_parent[tag_type])
	return search_groups


def group_tags_for_edit(tags, tag_types=None):
	tag_parent = {tag_type['label']:{'admin_administrated': tag_type['admin_administrated'], 'type_name': tag_type['type_name']} for tag_type in tag_types['results']}
	for tag in tags:
		tag['text'] = tag['text']
		if 'tags' not in tag_parent[tag['tag_type']]:
			tag_parent[tag['tag_type']]['tags'] = []
			tag_parent[tag['tag_type']]['tags'].append(tag)
		else:
			tag_parent[tag['tag_type']]['tags'].append(tag)
	return tag_parent


def get_form_tags(request, form_dict, key, tags):
	tags = []
	tags_list = request.POST.getlist(key)
	type_label = key.split('_tags[]')[0]
	for t in tags_list:
		if not t.strip():
			continue
		tag = {'tag_type': type_label, 'text': t}
		tags.append(tag)
	form_dict.pop(key)
	return tags


def process_attributes(obj_attrs, all_attrs):
	obj_attrs = [attribute['name'] for attribute in obj_attrs]
	for attribute in all_attrs:
		for attribute_value in attribute['attribute_values']:
			if attribute_value['name'] in obj_attrs:
				attribute_value['checked'] = True
	return all_attrs


def get_attributes_from_form_data(request):
	obj_attributes = []
	attributes = request.POST.getlist('attributevals')
	for attribute in attributes:
		attribute_vals = attribute.split('|_|')
		if len(attribute_vals) > 1:
			obj_attributes.append({
				"attribute_type": attribute_vals[0],
				"name": attribute_vals[1]
			})
	return obj_attributes


def get_attributes_for_display(obj_attrs):
	attrs = {}
	attr_types = set()
	for attribute in obj_attrs:
		if attribute['attribute_type'] not in attr_types:
			attr_types.add(attribute['attribute_type'])
			attrs[attribute['attribute_type']] = []
		attrs[attribute['attribute_type']].append({'display_name': attribute['display_name'], 'id': attribute['id']})
	return attrs


def get_array_attributes_for_display(dict_array, attr_key):
	for obj in dict_array:
		obj[attr_key] = get_attributes_for_display(obj[attr_key])
	return dict_array


def sanitize_rich_text(rich_text):
	if rich_text is not None:
		rich_text = escape(rich_text)
	else:
		rich_text = ''
	return rich_text


def get_save_search_data(request):
	template_data = request.POST.copy()
	template_data = get_list_from_form('include_facets', template_data, request)
	template_data = get_list_from_form('exclude_facets', template_data, request)
	search_data = {
		'include_facets': str(template_data.get('include_facets', [])),
		'exclude_facets': str(template_data.get('exclude_facets', []))
	}
	info_facets = {}
	if template_data.get('word_count_lte', ''):
		info_facets['word_count_lte'] = template_data.get('word_count_lte')
	if template_data.get('word_count_gte', ''):
		info_facets['word_count_gte'] = template_data.get('word_count_gte')
	template_data = get_list_from_form('languages', template_data, request)
	info_facets['languages'] = template_data.get('languages', [])
	completes = []
	if template_data.get('complete', None) and int(template_data.get('complete')) > -1:
		completes.append(template_data.get('complete'))
	info_facets[search_constants.COMPLETE_FILTER_KEY] = completes
	template_data = get_list_from_form('work_types', template_data, request)
	info_facets[search_constants.WORK_TYPE_FILTER_KEY] = template_data.get('work_types', [])
	search_data['info_facets'] = str(info_facets)
	search_data['term'] = template_data.get('term', '')
	return search_data

def get_list_from_form(form_key, obj_dict, request):
	if f'{form_key}[]' in obj_dict:
		obj_dict[form_key] = [x for x in request.POST.getlist(f"{form_key}[]")]
		obj_dict.pop(f'{form_key}[]')
	return obj_dict


def populate_default_languages(languages, request):
	for language in languages:
		for default_language in request.user.default_languages.all():
			if default_language.id == language['id']:
				language['selected'] = True
	return languages


def get_work_obj(request, work_id=None):
	work_dict = request.POST.copy()
	publish_all = False
	if 'publish_all' in work_dict:
		publish = work_dict.pop('publish_all')
		if publish[0].lower() == 'on':
			publish_all = True
	if 'preferred_download_url' in work_dict and work_dict['preferred_download_url'] == 'None':
		work_dict['preferred_download_url'] = ''
	if 'preferred_download' in work_dict and work_dict['preferred_download'] == 'None':
		work_dict.pop('preferred_download')
	work_dict = get_list_from_form('languages', work_dict, request)
	multichapter = work_dict.pop('multichapter') if 'multichapter' in work_dict else None
	chapter_dict = {
		'title': '',
		'summary': '',
		'notes': '',
		'number': '1',
		'image_url': '',
		'image_url-upload': '',
		'image_alt_text': '',
		'audio_url': '',
		'audio_url-upload': '',
		'audio_description': '',
		'video_url': '',
		'video_url-upload': '',
		'text': '',
		'work': '',
		'draft': "true" if 'chapter_draft' in request.POST else "false",
		'end_notes': '',
		'created_on': str(datetime.now().date()),
		'updated_on': str(datetime.now().date())
	}
	tags = []
	tag_types = {}
	chapters = []
	users = []
	result = do_get(f'api/tagtypes', request)
	for item in result.response_data['results']:
		tag_types[item['type_name']] = item
	for item in request.POST:
		if item in chapter_dict and not multichapter:
			val_list = request.POST.getlist(item)
			if len(val_list) > 1:
				chapter_dict[item] = val_list[1]
				work_dict[item] = val_list[0]
			else:
				chapter_dict[item] = request.POST[item]
		elif item in chapter_dict:
			val_list = request.POST.getlist(item)
			if len(val_list) > 1:
				work_dict[item] = val_list[0]
		elif item == 'chapter_id':
			chapter_dict['id'] = request.POST[item]
			work_dict.pop('chapter_id')
		elif '_tags[]' in item:
			tags = tags + get_form_tags(request, work_dict, item, tags)
		elif 'chapters_' in item and work_id is not None:
			chapter_id = item[9:]
			chapter_number = request.POST[item]
			chapters.append({'id': chapter_id, 'number': chapter_number, 'work': work_id})
		elif item.startswith('work_cocreators_'):
			user_id = item[16:]
			users.append(user_id)
	work_dict["users_to_add"] = users
	work_dict["tags"] = tags
	chapter_dict = None if multichapter else chapter_dict
	if work_id and chapter_dict:
		chapter_dict['work'] = work_id
	if 'comments_permitted' not in work_dict:
		comments_permitted = False
	else:
		comments_permitted = work_dict["comments_permitted"]
		work_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
	work_dict["anon_comments_permitted"] = comments_permitted == "All"
	redirect_toc = work_dict.pop('redirect_toc')[0]
	work_dict["is_complete"] = "is_complete" in work_dict
	work_dict["draft"] = "true" if "work_draft" in work_dict else "false"
	work_dict = work_dict.dict()
	work_dict["user"] = str(request.user)
	work_dict["attributes"] = get_attributes_from_form_data(request)
	if not work_dict.get('created_on', ''):
		work_dict["created_on"] = str(datetime.now().date())
	if not work_dict.get('updated_on', ''):
		work_dict["updated_on"] = str(datetime.now().date())
	else:
		if work_dict["updated_on"] == work_dict["updated_on_original"]:
			work_dict["updated_on"] = str(datetime.now().date())
	work_dict.pop('updated_on_original')
	if chapter_dict and not chapter_dict.get('created_on', ''):
		chapter_dict["created_on"] = str(datetime.now().date())
	if chapter_dict and not chapter_dict.get('updated_on', ''):
		chapter_dict["updated_on"] = str(datetime.now().date())
	else:
		if chapter_dict and chapter_dict.get("updated_on", "") == chapter_dict.get("updated_on_original", ""):
			chapter_dict["updated_on"] = str(datetime.now().date())
			chapter_dict.pop('updated_on_original')
	series_id = work_dict.get('series_id', None)
	if series_id and not series_id.isdigit():
		work_dict.pop('series_id')
	return [work_dict, redirect_toc, chapters, chapter_dict, publish_all, series_id]


def create_work_series(request, title, work_id):
	new_series = {
		"user": request.user.username,
		"works": [work_id],
		"title": title,
		"description": "",
		"is_complete": False
	}
	series_response = do_post(f'api/series/', request, new_series, 'Series')
	return series_response.response_data.get('id', None)


def get_bookmark_obj(request):
	bookmark_dict = request.POST.copy()
	tags = []
	tag_types = {}
	result = do_get(f'api/tagtypes', request)
	for item in result.response_data['results']:
		tag_types[item['type_name']] = item
	for item in request.POST:
		if '_tags[]' in item:
			tags = tags + get_form_tags(request, bookmark_dict, item, tags)
	bookmark_dict["tags"] = tags
	comments_permitted = bookmark_dict["comments_permitted"]
	bookmark_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
	bookmark_dict["anon_comments_permitted"] = comments_permitted == "All"
	bookmark_dict = bookmark_dict.dict()
	bookmark_dict["user"] = str(request.user)
	bookmark_dict["draft"] = 'true' if 'draft' in bookmark_dict else 'false'
	bookmark_dict["is_private"] = 'true' if 'is_private' in bookmark_dict else 'false'
	bookmark_dict["attributes"] = get_attributes_from_form_data(request)
	if bookmark_dict["updated_on"] == bookmark_dict["updated_on_original"]:
		bookmark_dict["updated_on"] = str(datetime.now().date())
	bookmark_dict.pop("updated_on_original")
	bookmark_dict = get_list_from_form('languages', bookmark_dict, request)
	return bookmark_dict


def get_bookmark_collection_obj(request):
	collection_dict = request.POST.copy()
	tags = []
	bookmarks = []
	tag_types = {}
	users = []
	result = do_get(f'api/tagtypes', request)
	for item in result.response_data['results']:
		tag_types[item['type_name']] = item
	for item in request.POST:
		if '_tags[]' in item:
			tags = tags + get_form_tags(request, collection_dict, item, tags)
		if 'workidstoadd' in request.POST[item]:
			json_item = request.POST[item].split("_")
			if len(json_item) < 2:
				continue
			bookmark_id = json_item[1]
			bookmarks.append(bookmark_id)
			collection_dict.pop(item)
		elif item.startswith('collection_cocreators_'):
			user_id = item[22:]
			users.append(user_id)
	collection_dict["users_to_add"] = users
	collection_dict["tags"] = tags
	collection_dict["works"] = bookmarks
	comments_permitted = collection_dict["comments_permitted"]
	collection_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
	collection_dict["anon_comments_permitted"] = comments_permitted == "All"
	collection_dict = collection_dict.dict()
	collection_dict["user"] = str(request.user)
	collection_dict["draft"] = 'true' if 'draft' in collection_dict else 'false'
	collection_dict["is_private"] = 'false'
	collection_dict["attributes"] = get_attributes_from_form_data(request)
	if collection_dict["updated_on"] == collection_dict["updated_on_original"]:
		collection_dict["updated_on"] = str(datetime.now().date())
	collection_dict.pop("updated_on_original")
	collection_dict = get_list_from_form('languages', collection_dict, request)
	return collection_dict


def get_series_obj(request):
	series_dict = request.POST.copy()
	works = []
	for item in request.POST:
		if 'workidstoadd' in request.POST[item]:
			json_item = request.POST[item].split("_")
			if len(json_item) < 2:
				continue
			work_id = json_item[1]
			works.append(work_id)
			series_dict.pop(item)
	series_dict["works"] = works
	series_dict["user"] = str(request.user)
	if series_dict["updated_on"] == series_dict["updated_on_original"]:
		series_dict["updated_on"] = str(datetime.now().date())
	series_dict.pop("updated_on_original")
	if not series_dict["updated_on"]:
		series_dict.pop("updated_on")
	if not series_dict["created_on"]:
		series_dict.pop("created_on")
	series_dict["is_complete"] = "is_complete" in series_dict
	return series_dict


def get_work_order_nums(ordering_dict, order_key):
	work_ids = []
	series_tracker = 1
	for key in ordering_dict.keys():
		if key.startswith(f'work_{order_key}_'):
			work_id = key.replace(f'work_{order_key}_', '')
			work_ids.append({
				'work': work_id,
				order_key: series_tracker
			})
			series_tracker = series_tracker + 1
	return work_ids


def get_anthology_obj(request):
	anthology_dict = request.POST.copy()
	works = []
	tags = []
	tag_types = {}
	users = []
	result = do_get(f'api/tagtypes', request)
	for item in result.response_data['results']:
		tag_types[item['type_name']] = item
	for item in request.POST:
		if 'workidstoadd' in request.POST[item]:
			json_item = request.POST[item].split("_")
			if len(json_item) < 2:
				continue
			work_id = json_item[1]
			works.append(work_id)
			anthology_dict.pop(item)
		elif '_tags[]' in item:
			tags = tags + get_form_tags(request, anthology_dict, item, tags)
		elif item.startswith('anthology_cocreators_'):
			user_id = item[21:]
			users.append(user_id)
	anthology_dict = get_list_from_form('languages', anthology_dict, request)
	anthology_dict["users_to_add"] = users
	anthology_dict["works"] = works
	anthology_dict["tags"] = tags
	anthology_dict["creating_user"] = str(request.user)
	if anthology_dict["updated_on"] == anthology_dict["updated_on_original"]:
		anthology_dict["updated_on"] = str(datetime.now().date())
	anthology_dict.pop("updated_on_original")
	if not anthology_dict["updated_on"]:
		anthology_dict.pop("updated_on")
	if not anthology_dict["created_on"]:
		anthology_dict.pop("created_on")
	anthology_dict["is_complete"] = "is_complete" in anthology_dict
	anthology_dict["attributes"] = get_attributes_from_form_data(request)
	return anthology_dict


def prepare_chapter_data(chapter, request):
	if 'text' in chapter:
		chapter['text'] = sanitize_rich_text(chapter['text'])
		chapter['text'] = chapter['text'].replace('\r\n', '<br/>')
	if 'summary' in chapter:
		chapter['summary'] = sanitize_rich_text(chapter['summary'])
	if 'notes' in chapter:
		chapter['notes'] = sanitize_rich_text(chapter['notes'])
		chapter['notes'] = chapter['notes'].replace('\r\n', '<br/>')
	if 'end_notes' in chapter:
		chapter['end_notes'] = sanitize_rich_text(chapter['end_notes'])
		chapter['notes'] = chapter['notes'].replace('\r\n', '<br/>')
	og_attributes = chapter['attributes'] if 'attributes' in chapter else []
	chapter_attributes = do_get(f'api/attributetypes', request, params={'allow_on_chapter': True}, object_name='Attribute')
	chapter['attribute_types'] = process_attributes(og_attributes, chapter_attributes.response_data['results'])
	return chapter


def get_bookmark_boilerplate(request, work_id):
	tag_types = do_get(f'api/tagtypes', request, 'Tag Type').response_data
	if not request.user.copy_work_metadata:
		tags = group_tags_for_edit([], tag_types)
	else:
		work = do_get(f'api/works/{work_id}', request, 'Work').response_data
		tags = group_tags_for_edit(work['tags'], tag_types) if work and 'tags' in work else group_tags_for_edit([], tag_types)
		title = work['title'] if work else ''
	bookmark = {
		'title': title if request.user.copy_work_metadata else '',
		'description': '',
		'user': request.user.username,
		'work': {'title': request.GET.get('title'), 'id': work_id},
		'anon_comments_permitted': True,
		'comments_permitted': True,
		'created_on': str(datetime.now().date()),
		'updated_on': str(datetime.now().date())
	}
	bookmark_attributes = do_get(f'api/attributetypes', request, params={'allow_on_bookmark': True}, object_name='Attribute')
	bookmark['attribute_types'] = process_attributes([], bookmark_attributes.response_data['results'])
	# todo - this should be a specific endpoint, we don't need to retrieve 10 objects to get config
	star_count = do_get(f'api/bookmarks', request, 'Bookmark').response_data['star_count']
	bookmark['rating'] = star_count
	return [bookmark, tags, star_count]


# utility method to format date for the Django template engine.
# there should be a better way to do this. google was not forthcoming.
def format_date_for_template(obj, field_name, is_list=False):
	if not is_list and field_name not in obj:
		return obj
	if is_list:
		for item in obj:
			if not item.get(field_name):
				continue
			item[field_name] = parse(item[field_name]).date()
		return obj
	try:
		obj[field_name] = parse(obj[field_name]).date() if obj[field_name] is not None else None
	except Exception as ex:
		logger.error(f"Error formatting date for template: {ex}")
	return obj


def get_owns_object(obj, request, key='users', creating_key='user_id'):
	return any(user['username'] == request.user.username for user in obj[key]) or obj.get('user_id', 0) == request.user.id


def format_comments_for_template(comments):
	for comment in comments:
		comment = format_date_for_template(comment, 'updated_on')
		if comment['replies']:
			comment['replies'] = format_comments_for_template(comment['replies'])
	return comments


def referrer_redirect(request, alternate_url=None):
	response = None
	if request.META.get('HTTP_REFERER') is not None:
		if not any(loc in request.META['HTTP_REFERER'] for loc in ['/login', '/register', '/reset']):
			response = redirect(f"{request.META.get('HTTP_REFERER')}")
		else:
			refer = alternate_url if alternate_url is not None else '/'
			response = redirect(f"{refer}")
	else:
		response = redirect('/')
	return response


def get_object_tags(parent):
	for item in parent:
		item['tags'] = group_tags(item['tags']) if 'tags' in item else {}
	return parent


def get_unauthorized_message(request, redirect_url, html_tag):
	messages.add_message(request, messages.WARNING, _('You must log in to perform this action.'), html_tag)
	return redirect(redirect_url)


def process_message(request, response):
	message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
	messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)


def get_works_list(request, username=None):
	url = f'api/users/{username}/works' if username is not None else f'api/works'
	response = do_get(url, request, params=request.GET, object_name='User Works')
	if response.response_info.status_code >= 400:
		messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
		return redirect('/')
	else:
		works = response.response_data['results']
		works = get_object_tags(works)
		works = format_date_for_template(works, 'updated_on', True)
		for work in works:
			work['attributes'] = get_attributes_for_display(work.get('attributes', []))
	return {'count': response.response_data['count'], 'works': works, 'next_params': response.response_data['next_params'] if 'next_params' in response.response_data else None, 'prev_params': response.response_data['prev_params'] if 'prev_params' in response.response_data else None}


def convert_bool(post_data):
	for key in post_data.keys():
		if post_data[key] == 'on':
			post_data[key] = 'true'
	return post_data


def get_languages(request):
	return do_get(f'api/languages', request, params={}, object_name='Languages').response_data.get('results', [])


def process_languages(languages, obj_languages, str_array=False):
	for language in languages:
		language['selected'] = False
		for obj_language in obj_languages:
			if str_array:
				if language.get('display_name', None) == obj_language:
					language['selected'] = True
			else:
				if language.get('display_name', None) == obj_language.get('display_name'):
					language['selected'] = True
	return deepcopy(languages)


def get_work_types(request):
	return do_get(f'api/worktypes', request, {}, 'Work Type').response_data.get('results', [])


def create_browse_cards(request):
	work_types = get_work_types(request)
	tag_types = do_get(f'api/tagtypes/browsable', request, {}, 'Tag Type').response_data.get('results', [])
	attribute_types = do_get(f'api/attributetypes/browsable', request, {}, 'Attribute Type').response_data.get('results', [])
	browse_cards = [{'label': 'Work Types', 'cards': []}]
	for wt in work_types:
		browse_cards[0]['cards'].append({
			'label': wt['type_name'],
			'url': f'/search/?work_type_id={wt["id"]}',
			'id': f'{wt["id"]}'
		})
	for tt in tag_types:
		tag_type = {
			'label': tt['label'],
			'cards': []
		}
		tags = do_get(f'api/tagtypes/browsable/tags', request, {'tag_type': tt['id']}, 'Tag Type').response_data.get('results', [])
		for tag in tags:
			tag_type['cards'].append({
				'label': tag['display_text'],
				'id': tag['id'],
				'url': f'/tags/{tag["id"]}?tag_id={tag["id"]}'
			})
		browse_cards.append(tag_type)
	for at in attribute_types:
		attribute_type = {
			'label': at['display_name'],
			'cards': []
		}
		for attribute in at['attribute_values']:
			attribute_type['cards'].append({
				'label': attribute['display_name'],
				'id': attribute['id'],
				'url': f'/attributes/{attribute["id"]}?attr_id={attribute["id"]}'
			})
		browse_cards.append(attribute_type)
	return browse_cards


def get_news(request):
	return do_get(f'api/news', request, {}, 'News')


def get_series_users(request, series):
	series['owner'] = request.user.id == series['user_id']
	users = set()
	series['users'] = []
	for work in series['works_readonly']:
		for user in work['users']:
			if user['username'] not in users:
				users.add(user['username'])
				series['users'].append(user)
	return series


def get_anthology_users(request, anthology):
	anthology['owner'] = request.user.id == anthology['creating_user_id']
	if not anthology['owner']:
		for owner in anthology['owners']:
			if owner['id'] == request.user.id:
				anthology['owner'] = True
				break
	return anthology


def get_saved_search_chive_info(saved_search, work_types):
	search_work_types = saved_search.get('info_facets_json', {}).get(search_constants.WORK_TYPE_FILTER_KEY, [])
	for work_type in work_types:
		if work_type.get('type_name') in search_work_types:
			work_type['checked'] = True
	saved_search['work_types'] = work_types
	saved_search['word_count_gte'] = saved_search.get('info_facets_json', {}).get(search_constants.WORD_COUNT_FILTER_KEY_GTE)
	saved_search['word_count_lte'] = saved_search.get('info_facets_json', {}).get(search_constants.WORD_COUNT_FILTER_KEY_LTE)
	saved_search['work_statuses'] = saved_search.get('info_facets_json', {}).get(search_constants.COMPLETE_FILTER_KEY, [])
	return saved_search


def get_pagination_array(pages):
	pagination_array = [1, 2, 3, 4, 5, '...', pages] if pages > 5 else [x+1 for x in range(0, pages)]
	return pagination_array
