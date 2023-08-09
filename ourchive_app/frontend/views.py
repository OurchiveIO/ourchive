from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, logout, login
from django.contrib import messages
from .search_models import SearchObject
from html import escape, unescape
from django.http import HttpResponse, FileResponse
import logging
from .api_utils import do_get, do_post, do_patch, do_delete, validate_captcha
from django.utils.translation import gettext as _
from api import utils
from django.views.decorators.cache import never_cache
from dateutil.parser import *

logger = logging.getLogger(__name__)


def group_tags(tags):
	tag_parent = {}
	for tag in tags:
		if tag['tag_type'] not in tag_parent:
			tag_parent[tag['tag_type']] = [tag]
		else:
			tag_parent[tag['tag_type']].append(tag)
	return tag_parent


def group_tags_for_edit(tags, tag_types=None):
	tag_parent = {tag_type['label']:{'admin_administrated': tag_type['admin_administrated']} for tag_type in tag_types['results']}
	for tag in tags:
		tag['text'] = escape(tag['text'])
		if 'tags' not in tag_parent[tag['tag_type']]:
			tag_parent[tag['tag_type']]['tags'] = []
			tag_parent[tag['tag_type']]['tags'].append(tag)
		else:
			tag_parent[tag['tag_type']]['tags'].append(tag)
	return tag_parent


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
		attrs[attribute['attribute_type']].append(attribute['display_name'])
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


def get_work_obj(request, work_id=None):
	work_dict = request.POST.copy()
	tags = []
	tag_types = {}
	chapters = []
	result = do_get(f'api/tagtypes', request)
	for item in result.response_data['results']:
		tag_types[item['label']] = item
	for item in request.POST:
		if 'tags' in request.POST[item]:
			tag = {}
			json_item = request.POST[item].split("_")
			tag['tag_type'] = json_item[2]
			tag['text'] = json_item[1]
			tags.append(tag)
			work_dict.pop(item)
		elif 'chapters_' in item and work_id is not None:
			chapter_id = item[9:]
			chapter_number = request.POST[item]
			chapters.append({'id': chapter_id, 'number': chapter_number, 'work': work_id})
	work_dict["tags"] = tags
	if 'comments_permitted' not in work_dict:
		comments_permitted = False
	else:
		comments_permitted = work_dict["comments_permitted"]
		work_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
	work_dict["anon_comments_permitted"] = comments_permitted == "All"
	redirect_toc = work_dict.pop('redirect_toc')[0]
	work_dict["is_complete"] = "is_complete" in work_dict
	work_dict["draft"] = "draft" in work_dict
	work_dict = work_dict.dict()
	work_dict["user"] = str(request.user)
	work_dict["attributes"] = get_attributes_from_form_data(request)
	return [work_dict, redirect_toc, chapters]


def get_bookmark_obj(request):
	bookmark_dict = request.POST.copy()
	tags = []
	tag_types = {}
	result = do_get(f'api/tagtypes', request)
	for item in result.response_data['results']:
		tag_types[item['label']] = item
	for item in request.POST:
		if 'tags' in request.POST[item]:
			tag = {}
			json_item = request.POST[item].split("_")
			tag['tag_type'] = json_item[2]
			tag['text'] = json_item[1]
			tags.append(tag)
			bookmark_dict.pop(item)
	bookmark_dict["tags"] = tags
	comments_permitted = bookmark_dict["comments_permitted"]
	bookmark_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
	bookmark_dict["anon_comments_permitted"] = comments_permitted == "All"
	bookmark_dict = bookmark_dict.dict()
	bookmark_dict["user"] = str(request.user)
	bookmark_dict["draft"] = 'draft' in bookmark_dict
	bookmark_dict["attributes"] = get_attributes_from_form_data(request)
	return bookmark_dict


def get_bookmark_collection_obj(request):
	collection_dict = request.POST.copy()
	tags = []
	bookmarks = []
	tag_types = {}
	result = do_get(f'api/tagtypes', request)
	for item in result.response_data['results']:
		tag_types[item['label']] = item
	for item in request.POST:
		if 'tags' in request.POST[item]:
			tag = {}
			json_item = request.POST[item].split("_")
			tag['tag_type'] = json_item[2]
			tag['text'] = json_item[1]
			tags.append(tag)
			collection_dict.pop(item)
		if 'bookmarksidstoadd' in request.POST[item]:
			json_item = request.POST[item].split("_")
			if len(json_item) < 2:
				continue
			bookmark_id = json_item[1]
			bookmarks.append(bookmark_id)
			collection_dict.pop(item)
	collection_dict["tags"] = tags
	collection_dict["bookmarks"] = bookmarks
	comments_permitted = collection_dict["comments_permitted"]
	collection_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
	collection_dict["anon_comments_permitted"] = comments_permitted == "All"
	collection_dict = collection_dict.dict()
	collection_dict["user"] = str(request.user)
	collection_dict["draft"] = 'draft' in collection_dict
	collection_dict["is_private"] = False
	collection_dict["attributes"] = get_attributes_from_form_data(request)
	return collection_dict


def get_default_search_result_tab(resultsets):
	most_results = 0
	default_tab = ''
	for results in resultsets:
		if len(results[0]) > most_results:
			most_results = len(results[0])
			default_tab = results[1]
	return default_tab


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
	return {'works': works, 'next_params': response.response_data['next_params'] if 'next_params' in response.response_data else None, 'prev_params': response.response_data['prev_params'] if 'prev_params' in response.response_data else None}


def index(request):
	return render(request, 'index.html', {
		'heading_message': _('ourchive_welcome'),
		'long_message': _('ourchive_intro_copy'),
		'root': settings.ROOT_URL,
		'stylesheet_name': 'ourchive-light.css',
		'has_notifications': request.session.get('has_notifications')
	})


def accept_cookies(request):
	if request.user.is_authenticated:
		do_patch(f'api/users/{request.user.id}/', request, data={'id': request.user.id, 'cookies_accepted': True})
	return HttpResponse('')


def content_page(request, pk):
	response = do_get(f'api/contentpages/{pk}', request, params=request.GET)
	if response.response_info.status_code == 403:
		messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
		return redirect('/')
	return render(request, 'content_page.html', {
		'content_page': response.response_data
	})


def user_name(request, username):
	user = do_get(f"api/users/{username}", request, 'User')
	if user.response_info.status_code >= 400:
		messages.add_message(request, messages.ERROR, user.response_info.message, user.response_info.type_label)
		return redirect('/')
	work_params = {}
	bookmark_params = {}
	bookmark_collection_params = {}
	anchor = None
	if 'work_offset' in request.GET:
		work_params['offset'] = request.GET['work_offset']
		work_params['limit'] = request.GET['work_limit']
		anchor = "work_tab"
	if 'bookmark_offset' in request.GET:
		bookmark_params['offset'] = request.GET['bookmark_offset']
		bookmark_params['limit'] = request.GET['bookmark_limit']
		anchor = "bookmark_tab"
	if 'bookmark_collection_offset' in request.GET:
		bookmark_collection_params['offset'] = request.GET['bookmark_collection_offset']
		bookmark_collection_params['limit'] = request.GET['bookmark_collection_limit']
		anchor = "bookmark_collection_tab"
	works_response = do_get(f'api/users/{username}/works', request, params=work_params, object_name='Works')
	works = works_response.response_data['results']
	works = get_object_tags(works)
	work_next = f'/username/{username}/{works_response.response_data["next_params"].replace("limit=", "work_limit=").replace("offset=", "work_offset=")}' if works_response.response_data["next_params"] is not None else None
	work_previous = f'/username/{username}/{works_response.response_data["prev_params"].replace("limit=", "work_limit=").replace("offset=", "work_offset=")}' if works_response.response_data["prev_params"] is not None else None
	bookmarks_response = do_get(f'api/users/{username}/bookmarks', request, params=bookmark_params).response_data
	bookmarks = bookmarks_response['results']
	bookmark_next = f'/username/{username}/{bookmarks_response["next_params"].replace("limit=", "bookmark_limit=").replace("offset=", "bookmark_offset=")}' if bookmarks_response["next_params"] is not None else None
	bookmark_previous = f'/username/{username}/{bookmarks_response["prev_params"].replace("limit=", "bookmark_limit=").replace("offset=", "bookmark_offset=")}' if bookmarks_response["prev_params"] is not None else None
	bookmarks = get_object_tags(bookmarks)
	bookmark_collection_response = do_get(f'api/users/{username}/bookmarkcollections', request, params=bookmark_collection_params).response_data
	bookmark_collection = bookmark_collection_response['results']
	bookmark_collection_next = f'/username/{username}/{bookmark_collection_response["next_params"].replace("limit=", "bookmark_collection_limit=").replace("offset=", "bookmark_collection_offset=")}' if bookmark_collection_response["next_params"] is not None else None
	bookmark_collection_previous = f'/username/{username}/{bookmark_collection_response["prev_params"].replace("limit=", "bookmark_collection_limit=").replace("offset=", "bookmark_collection_offset=")}' if bookmark_collection_response["prev_params"] is not None else None
	bookmark_collection = get_object_tags(bookmark_collection)
	user = user.response_data['results'][0]
	user['attributes'] = get_attributes_for_display(user['attributes'])
	subscription = do_get(f"api/subscriptions/", request, params={'subscribed_to': username}, object_name='Subscription')
	if 'results' in subscription.response_data and len(subscription.response_data['results']) > 0:
		subscription = subscription.response_data['results'][0]
	else:
		subscription = None
	return render(request, 'user.html', {
		'bookmarks': bookmarks,
		'bookmarks_next': bookmark_next,
		'bookmarks_previous': bookmark_previous,
		'user_filter': username,
		'root': settings.ROOT_URL,
		'works': works,
		'anchor': anchor,
		'works_next': work_next,
		'works_previous': work_previous,
		'bookmark_collections': bookmark_collection,
		'bookmark_collections_next': bookmark_collection_next,
		'bookmark_collections_previous': bookmark_collection_previous,
		'user': user,
		'subscription' : subscription
	})


def import_works(request, username):
	if not request.user.is_authenticated:
		messages.add_message(request, messages.ERROR, _('You must be logged in to import works.'), 'Import')
		return redirect('/')
	if request.method == 'POST':
		referer = request.POST.get('referer')
		allow_anon_comments = request.POST.get('allow_anon_comments') == 'on'
		allow_comments = request.POST.get('allow_comments') == 'on'
		save_as_draft = request.POST.get('save_as_draft') == 'on'
		data = {
			'allow_anon_comments': allow_anon_comments,
			'allow_comments': allow_comments,
			'save_as_draft': save_as_draft
		}
		if 'mode' in request.POST:
			data['work_id'] = request.POST.get('work_id', '')
		else:
			data['username'] = request.POST.get('username', '')
		response = do_post(f'api/users/import-works/', request, data, 'Import')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, _('Import has started. You will receive a notification when it completes.'), response.response_info.type_label)
		return redirect(referer)
	return render(request, 'work_import_form.html', {
		'form_title': _('Import Work(s)'),
		'referer': request.META.get('HTTP_REFERER')
		})


def user_block_list(request, username):
	blocklist = do_get(f'api/users/{username}/userblocks', request, 'Blocklist')
	if blocklist.response_info.status_code >= 400:
		messages.add_message(request, messages.ERROR, blocklist.response_info.message, blocklist.response_info.type_label)
		return redirect(f'/username/{username}')
	return render(request, 'user_block_list.html', {
		'blocklist': blocklist.response_data['results'],
		'username': username
	})


def block_user(request, username):
	data = {'user': request.user.username, 'blocked_user': username}
	blocklist = do_post(f'api/userblocks', request, data, 'Block')
	message_type = messages.WARNING
	if blocklist.response_info.status_code >= 400:
		message_type = messages.ERROR
	elif blocklist.response_info.status_code >= 200:
		message_type = messages.SUCCESS
	messages.add_message(request, message_type, blocklist.response_info.message, blocklist.response_info.type_label)
	return redirect(f'/username/{username}')


def unblock_user(request, username, pk):
	blocklist = do_delete(f'api/userblocks/{pk}', request, 'Blocklist')
	message_type = messages.WARNING
	if blocklist.response_info.status_code >= 400:
		message_type = messages.ERROR
	elif blocklist.response_info.status_code >= 200:
		message_type = messages.SUCCESS
	messages.add_message(request, message_type, blocklist.response_info.message, blocklist.response_info.type_label)
	return redirect(f'/username/{username}')


def report_user(request, username):
	if request.method == 'POST':
		report_data = request.POST.copy()
		# we don't want to let the user specify this
		report_data['user'] = request.user.username
		response = do_post(f'api/userreports/', request, data=report_data, object_name='User Report')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		return redirect(f'/username/{username}/')
	else:
		if request.user.is_authenticated:
			report_reasons = do_get(f'api/reportreasons/', request, 'Report Reason').response_data
			return render(request, 'user_report_form.html', {
				'reported_user': username,
				'form_title': 'Report User',
				'report_reasons': report_reasons['reasons']
			})
		else:
			messages.add_message(request, messages.ERROR, _('You must log in to perform this action.'), 'report-user-unauthorized-error')
			return redirect('/login')


def user_works(request, username):
	works = get_works_list(request, username)
	return render(request, 'works.html', {
		'works': works['works'],
		'next': f"/username/{username}/works/{works['next_params']}" if works["next_params"] is not None else None,
		'previous': f"/username/{username}/works/{works['prev_params']}" if works["prev_params"] is not None else None,
		'user_filter': username,
		'root': settings.ROOT_URL})


def user_works_drafts(request, username):
	response = do_get(f'api/users/{username}works/drafts', request)
	works = response.response_data['results']
	works = get_object_tags(works)
	return render(request, 'works.html', {
		'works': works,
		'user_filter': username,
		'root': settings.ROOT_URL})


def edit_account(request, username):
	if request.method == 'POST':
		user_data = request.POST.copy()
		profile_id = user_data['id']
		user_data.pop('id')
		response = do_patch(f'api/users/{profile_id}/', request, data=user_data, object_name='Account')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		return redirect('/username/{username}')
	else:
		if request.user.is_authenticated:
			response = do_get(f'api/users/{username}', request)
			user = response.response_data['results']
			if len(user) > 0:
				user = user[0]
				return render(request, 'account_form.html', {'user': user})
			else:
				messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
				return redirect(f'/username/{username}')
		else:
			messages.add_message(request, messages.ERROR, _('You must log in as this user to perform this action.'), 'user-info-unauthorized-error')
			return redirect('/login')


def edit_user(request, username):
	if request.method == 'POST':
		user_data = request.POST.copy()
		if user_data['icon'] == "":
			user_data['icon'] = user_data['unaltered_icon']
		user_data.pop('unaltered_icon')
		user_id = user_data.pop('user_id')[0]
		user_data["attributes"] = get_attributes_from_form_data(request)
		response = do_patch(f'api/users/{user_id}/', request, data=user_data, object_name='User Profile')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		return redirect(f'/username/{username}/')
	else:
		if request.user.is_authenticated:
			response = do_get(f'api/users/{username}', request, 'User Profile')
			if response.response_info.status_code >= 400:
				messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
				return redirect(f'/username/{username}')
			user = response.response_data['results']
			user = user[0]
			if user is not None:
				user['profile'] = sanitize_rich_text(user['profile'])
			user_attributes = do_get(f'api/attributetypes', request, params={'allow_on_user': True}, object_name='Attribute')
			user['attribute_types'] = process_attributes(user['attributes'], user_attributes.response_data['results'])
			return render(request, 'user_form.html', {'user': user, 'form_title': 'Edit User'})
		else:
			messages.add_message(request, messages.ERROR, _('You must log in as this user to perform this action.'), 'user-profile-unauthorized-error')
			return redirect('/login')


def delete_user(request, username):
	if not request.user.is_authenticated:
		if 'HTTP_REFERER' in request.META and 'delete' not in request.META.get('HTTP_REFERER'):
			return referrer_redirect(request)
		else:
			if 'delete' not in request.META.get('HTTP_REFERER') and 'account/edit' not in request.META.get('HTTP_REFERER'):
				# you get to the button through the account edit screen, so we don't want to flash a warning if they came through here
				messages.add_message(request, messages.WARNING, _('You are not authorized to view this page.'), 'account-delete-unauthorized-error')
			return redirect('/')
	elif request.method == 'POST':
		response = do_delete(f'api/users/{request.user.id}', request, 'Account')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		return referrer_redirect(request)
	else:
		return render(request, 'delete_account.html', {'user': request.user})


def user_bookmarks(request, username):
	response = do_get(f'api/users/{username}/bookmarks', request, params=request.GET, object_name='User Bookmarks')
	bookmarks = response.response_data['results']
	bookmarks = get_object_tags(bookmarks)
	return render(request, 'bookmarks.html', {
		'bookmarks': bookmarks,
		'next': f"/username/{username}/bookmarks/{response.response_data['next_params']}" if response.response_data["next_params"] is not None else None,
		'previous': f"/username/{username}/bookmarks/{response.response_data['prev_params']}" if response.response_data["prev_params"] is not None else None,
		'user_filter': username})


def user_bookmark_collections(request, username):
	response = do_get(f'api/users/{username}/bookmarkcollections', request, params=request.GET, object_name='Bookmark Collections')
	bookmark_collections = response.response_data['results']
	bookmark_collections = get_object_tags(bookmark_collections)
	return render(request, 'bookmark_collections.html', {
		'bookmark_collections': bookmark_collections,
		'next': f"/username/{username}/bookmarkcollections/{response.response_data['next_params']}" if response.response_data["next_params"] is not None else None,
		'previous': f"/username/{username}/bookmarkcollections/{response.response_data['prev_params']}" if response.response_data["prev_params"] is not None else None,
		'user_filter': username})


def user_notifications(request, username):
	response = do_get(f'api/users/{username}/notifications', request, params=request.GET, object_name='Notification')
	if response.response_info.status_code == 204 or response.response_info.status_code == 200:
		notifications = response.response_data['results']
		return render(request, 'notifications.html', {
			'notifications': notifications,
			'next': f"/username/{username}/notifications/{response.response_data['next_params']}" if response.response_data['next_params'] is not None else None,
			'previous': f"/username/{username}/notifications/{response.response_data['prev_params']}" if response.response_data['prev_params'] is not None else None})
	else:
		process_message(request, response)
	return redirect(f'/')


def delete_notification(request, username, notification_id):
	response = do_delete(f'api/notifications/{notification_id}', request, 'Notification')
	message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
	messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
	return redirect(f'/username/{username}/notifications')


def mark_notification_read(request, username, notification_id):
	data = {'id': notification_id, 'read': True}
	response = do_patch(f'api/notifications/{notification_id}/', request, data=data, object_name='Notification')
	message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
	messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
	return redirect(f'/username/{username}/notifications')


def user_bookmarks_drafts(request, username):
	response = do_get(f'api/users/{username}/bookmarks/drafts', request, 'User Bookmarks')
	bookmarks = response.response_data['results']
	bookmarks = get_object_tags(bookmarks)
	return render(request, 'bookmarks.html', {'bookmarks': bookmarks, 'user_filter': username})


def user_bookmark_subscriptions(request, username):
	response = do_get(f'api/users/{username}/subscriptions/bookmarks', request)
	return render(request, 'user_bookmark_subscriptions.html', {
		'bookmarks': response.response_data
	})


def user_collection_subscriptions(request, username):
	response = do_get(f'api/users/{username}/subscriptions/collections', request, params=request.GET)
	return render(request, 'user_collection_subscriptions.html', {
		'bookmark_collections': response.response_data,
		'next': f"/users/{username}/subscriptions/collections/{response.response_data['next_params']}" if response.response_data['next_params'] is not None else None,
		'previous': f"/users/{username}/subscriptions/collections/{response.response_data['prev_params']}" if response.response_data['prev_params'] is not None else None,
	})


def user_subscriptions(request, username):
	response = do_get(f'api/users/{username}/subscriptions', request, 'Subscription')
	return render(request, 'user_subscriptions.html', {
		'subscriptions': response.response_data['results'] if 'results' in response.response_data else {}
	})


def unsubscribe(request, username):
	subscription_id = request.POST.get('subscription_id')
	if request.POST.get('unsubscribe_all'):
		response = do_delete(f'api/subscriptions/{subscription_id}/', request, object_name='Subscription')
		process_message(request, response)
	else:
		patch_data = {}
		if request.POST.get('subscribed_to_bookmark'):
			patch_data['subscribed_to_bookmark'] = False
		if request.POST.get('subscribed_to_collection'):
			patch_data['subscribed_to_collection'] = False
		response = do_patch(f'api/subscriptions/{subscription_id}/', request, data=patch_data, object_name='Subscription')
		process_message(request, response)
	return referrer_redirect(request)


def subscribe(request):
	if not request.user.is_authenticated:
		messages.add_message(request, messages.ERROR, _('You must be logged in to subscribe to users.'), f'subscribe-not-logged-in')
		return redirect('/login')
	post_data = {}
	if 'subscription_id' in request.POST:
		post_data['id'] = request.POST.get('subscription_id')
	post_data['subscribed_to_bookmark'] = True if request.POST.get('subscribed_to_bookmark') else False
	post_data['subscribed_to_collection'] = True if request.POST.get('subscribed_to_collection') else False
	post_data['user'] = request.user.username
	post_data['subscribed_user'] = request.POST.get('subscribed_to')
	if 'subscription_id' in request.POST:
		response = do_patch(f'api/subscriptions/{post_data["id"]}/', request, data=post_data, object_name='Subscription')
	else:
		response = do_post(f'api/subscriptions/', request, data=post_data, object_name='Subscription')
	process_message(request, response)
	return referrer_redirect(request)


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
				request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]] = [([filter_details[2], filter_details[3]])]
			else:
				request_object['work_search'][f'{include_exclude}_filter'][filter_details[0]].append((filter_details[2], filter_details[3]))
		else:
			# TODO evaluate if this can be gotten rid of; do we have legitimate use cases that aren't a range?
			filter_options = key.split('|')
			for option in filter_options:
				print(option)
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
				elif filter_type == 'bookmark':
					if filter_details[0] in request_object['bookmark_search'][f'{include_exclude}_filter'] and len(request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]]) > 0:
						request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]].append(filter_details[1])
					else:
						request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]] = []
						request_object['bookmark_search'][f'{include_exclude}_filter'][filter_details[0]].append(filter_details[1])
	return [request_object, return_keys]


def search(request):
	if 'term' in request.GET:
		term = request.GET['term']
	elif 'term' in request.POST:
		term = request.POST['term']
	else:
		return redirect('/')
	request_builder = SearchObject()
	pagination = {'page': request.GET.get('page', 1), 'obj': request.GET.get('object_type', '')}
	request_object = request_builder.with_term(term, pagination)
	request_object = get_search_request(request, request_object, request_builder)
	response_json = do_post(f'api/search/', request, data=request_object[0]).response_data
	works = response_json['results']['work']
	works['data'] = get_object_tags(works['data'])
	works['data'] = get_array_attributes_for_display(works['data'], 'attributes')
	bookmarks = response_json['results']['bookmark']
	bookmarks['data'] = get_object_tags(bookmarks['data'])
	bookmarks['data'] = get_array_attributes_for_display(bookmarks['data'], 'attributes')
	tags = response_json['results']['tag']
	tags['data'] = group_tags(tags['data'])
	tag_count = len(response_json['results']['tag']['data'])
	users = response_json['results']['user']
	collections = response_json['results']['collection']
	collections['data'] = get_array_attributes_for_display(collections['data'], 'attributes')
	default_tab = get_default_search_result_tab(
		[
			[works['data'], 0],
			[bookmarks['data'], 1],
			[tags['data'], 3],
			[users['data'], 4],
			[collections['data'], 2]
		])
	return render(request, 'search_results.html', {
		'works': works, 'bookmarks': bookmarks,
		'tags': tags, 'users': users, 'tag_count': tag_count, 'collections': collections,
		'facets': response_json['results']['facet'],
		'default_tab': default_tab,
		'click_func': 'getFormVals(event)',
		'root': settings.ROOT_URL, 'term': term,
		'keys_include': request_object[1]['include'],
		'keys_exclude': request_object[1]['exclude']})


def tag_autocomplete(request):
	term = request.GET.get('text')
	params = {'term': term}
	params['type'] = request.GET.get('type') if 'type' in request.GET else ''
	params['fetch_all'] = request.GET.get('fetch_all') if 'fetch_all' in request.GET else ''
	response = do_get(f'api/tag-autocomplete', request, params, 'Tag')
	template = 'tag_autocomplete.html' if request.GET.get('source') == 'search' else 'edit_tag_autocomplete.html'
	return render(request, template, {
		'tags': response.response_data['results'],
		'fetch_all': params['fetch_all']})


def bookmark_autocomplete(request):
	term = request.GET.get('text')
	params = {'term': term}
	response = do_get(f'api/bookmark-autocomplete', request, params, 'Bookmark')
	template = 'bookmark_collection_autocomplete.html'
	return render(request, template, {
		'bookmarks': response.response_data['results']})


def search_filter(request):
	term = request.POST.get('term', '')
	if not term:
		return redirect('/')
	include_filter_any = 'any' if request.POST.get('include_any_all') == 'on' else 'all'
	exclude_filter_any = 'any' if request.POST.get('exclude_any_all') == 'on' else 'all'
	order_by = request.POST['order_by'] if 'order_by' in request.POST else None
	request_builder = SearchObject()
	request_object = request_builder.with_term(term, None, (include_filter_any, exclude_filter_any), order_by)
	request_object = get_search_request(request, request_object, request_builder)
	response_json = do_post(f'api/search/', request, data=request_object[0], object_name='Search').response_data
	# todo DRY - this is redundant w search method - move processing to its own method
	works = response_json['results']['work']
	works['data'] = get_object_tags(works['data'])
	works['data'] = get_array_attributes_for_display(works['data'], 'attributes')
	bookmarks = response_json['results']['bookmark']
	bookmarks['data'] = get_object_tags(bookmarks['data'])
	bookmarks['data'] = get_array_attributes_for_display(bookmarks['data'], 'attributes')
	tags = response_json['results']['tag']
	tags['data'] = group_tags(tags['data'])
	tag_count = len(response_json['results']['tag']['data'])
	users = response_json['results']['user']
	collections = response_json['results']['collection']
	collections['data'] = get_object_tags(collections['data'])
	collections['data'] = get_array_attributes_for_display(collections['data'], 'attributes')
	default_tab = get_default_search_result_tab(
		[
			[works['data'], 0],
			[bookmarks['data'], 1],
			[tags['data'], 3],
			[users['data'], 4],
			[collections['data'], 2]
		])
	return render(request, 'search_results.html', {
		'works': works, 'bookmarks': bookmarks,
		'tags': tags, 'users': users, 'tag_count': tag_count, 'collections': collections,
		'facets': response_json['results']['facet'],
		'root': settings.ROOT_URL, 'term': term,
		'default_tab': default_tab,
		'click_func': 'getFormVals(event)',
		'keys_include': request_object[1]['include'],
		'keys_exclude': request_object[1]['exclude']})


@require_http_methods(["GET"])
def works(request):
	response = do_get(f'api/works/', request, params=request.GET, object_name='Work')
	works_response = response.response_data
	works = response.response_data['results'] if 'results' in response.response_data else []
	works = get_object_tags(works)
	works = get_array_attributes_for_display(works, 'attributes')
	for work in works:
		work['updated_on'] = parse(work['updated_on']).date()
	return render(request, 'works.html', {
		'works': works,
		'next': f"/works/{works_response['next_params']}" if works_response['next_params'] is not None else None,
		'previous': f"/works/{works_response['prev_params']}" if works_response['prev_params'] is not None else None,
		'root': settings.ROOT_URL})


def works_by_type(request, type_id):
	response = do_get(f'api/worktypes/{type_id}/works', request, 'Work').response_data
	works = response['results']
	works = get_object_tags(works)
	return render(request, 'works.html', {
		'works': works,
		'root': settings.ROOT_URL})


def new_work(request):
	work_types = do_get(f'api/worktypes', request, 'Work').response_data
	if request.user.is_authenticated and request.method != 'POST':
		work = {'title': 'Untitled Work', 'user': request.user.username, 'download_choices': [
	        ('EPUB', 'EPUB'), ('M4B', 'M4B'), ('ZIP', 'ZIP'), ('M4A', 'M4A'),
	        ('MOBI', 'MOBI')
	    ]}
		tag_types = do_get(f'api/tagtypes', request, 'Tag').response_data
		tags = {result['label']:[] for result in tag_types['results']}
		work_attributes = do_get(f'api/attributetypes', request, params={'allow_on_work': True}, object_name='Work Attributes')
		work['attribute_types'] = process_attributes([], work_attributes.response_data['results'])
		return render(request, 'work_form.html', {
			'tags': tags,
			'form_title': 'New Work',
			'work_types': work_types['results'],
			'work': work})
	elif request.user.is_authenticated:
		work_data = get_work_obj(request)
		work = do_post(f'api/works/', request, work_data[0], 'Work').response_data
		if work_data[1] == 'false':
			return redirect(f'/works/{work["id"]}')
		else:
			return redirect(f'/works/{work["id"]}/chapters/new?count=0')
	else:
		messages.add_message(request, messages.ERROR, _('You must log in to post a new work.'), 'new-work-unauthorized-error')
		return redirect('/login')


def new_chapter(request, work_id):
	if request.user.is_authenticated and request.method != 'POST':
		count = request.GET.get('count') if request.GET.get('count') != '' else 0
		chapter = {'title': 'Untitled Chapter', 'work': work_id, 'text': '', 'number': int(count) + 1}
		chapter_attributes = do_get(f'api/attributetypes', request, params={'allow_on_chapter': True}, object_name='Chapter')
		chapter['attribute_types'] = process_attributes([], chapter_attributes.response_data['results'])
		return render(request, 'chapter_form.html', {
			'chapter': chapter,
			'form_title': 'New Chapter'})
	elif request.user.is_authenticated:
		chapter_dict = request.POST.copy()
		chapter_dict["draft"] = "draft" in chapter_dict
		chapter_dict["attributes"] = get_attributes_from_form_data(request)
		response = do_post(f'api/chapters/', request, data=chapter_dict, object_name='Chapter')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		redirect_url = f'/works/{work_id}/?offset={request.GET.get("from_work", 0)}' if 'from_work' in request.GET else f"/works/{work_id}/edit/#work-form-chapter-content-parent"
		return redirect(redirect_url)
	else:
		messages.add_message(request, messages.ERROR, _('You must log in to post a new chapter.'), 'chapter-create-login-error')
		return redirect('/login')


def edit_chapter(request, work_id, id):
	if request.method == 'POST':
		chapter_dict = request.POST.copy()
		chapter_dict["draft"] = "draft" in chapter_dict
		chapter_dict["attributes"] = get_attributes_from_form_data(request)
		response = do_patch(f'api/chapters/{id}/', request, data=chapter_dict, object_name='Chapter')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		redirect_url = f'/works/{work_id}/?offset={request.GET.get("from_work", 0)}' if 'from_work' in request.GET else f"/works/{work_id}/edit/#work-form-chapter-content-parent"
		return redirect(redirect_url)
	else:
		if request.user.is_authenticated:
			chapter = do_get(f'api/chapters/{id}', request, 'Chapter').response_data
			chapter['text'] = sanitize_rich_text(chapter['text'])
			chapter['text'] = chapter['text'].replace('\r\n', '<br/>')
			chapter['summary'] = sanitize_rich_text(chapter['summary'])
			chapter['notes'] = sanitize_rich_text(chapter['notes'])
			chapter_attributes = do_get(f'api/attributetypes', request, params={'allow_on_chapter': True}, object_name='Attribute')
			chapter['attribute_types'] = process_attributes(chapter['attributes'], chapter_attributes.response_data['results'])
			return render(request, 'chapter_form.html', {
				'chapter': chapter,
				'form_title': 'Edit Chapter'})
		else:
			messages.add_message(request, messages.ERROR, _('You must log in to perform this action.'), 'chapter-update-login-error')
			return redirect('/login')


def edit_work(request, id):
	if request.method == 'POST':
		work_dict = get_work_obj(request, id)
		chapters = work_dict[2]
		response = do_patch(f'api/works/{id}/', request, data=work_dict[0], object_name='Work')
		messages.add_message(request, messages.SUCCESS, response.response_info.message, response.response_info.type_label)
		if response.response_info.status_code == 200:
			for chapter in chapters:
				response = do_patch(f'api/chapters/{chapter["id"]}/', request, data=chapter, object_name='Work')
				if response.response_info.status_code >= 400:
					messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
		else:
			messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
		if work_dict[1] == 'false':
			return redirect(f'/works/{id}')
		else:
			return redirect(f'/works/{id}/chapters/new?count={len(chapters)}')
	else:
		if request.user.is_authenticated:
			work_types = do_get(f'api/worktypes', request, 'Work Type').response_data
			tag_types = do_get(f'api/tagtypes', request, 'Tag Type').response_data
			works_response = do_get(f'api/works/{id}/', request, 'Work')
			if works_response.response_info.status_code >= 400:
				messages.add_message(request, messages.ERROR, works_response.response_info.message, works_response.response_info.type_label)
				return redirect('/')
			work = works_response.response_data
			work['summary'] = sanitize_rich_text(work['summary'])
			work['notes'] = sanitize_rich_text(work['notes'])
			work_attributes = do_get(f'api/attributetypes', request, params={'allow_on_work': True}, object_name='Attribute')
			work['attribute_types'] = process_attributes(work['attributes'], work_attributes.response_data['results'])
			chapters = do_get(f'api/works/{id}/chapters/all', request, 'Chapter').response_data
			tags = group_tags_for_edit(work['tags'], tag_types) if 'tags' in work else []
			return render(request, 'work_form.html', {
				'work_types': work_types['results'],
				'form_title': 'Edit Work',
				'work': work,
				'tags': tags,
				'show_chapter': request.GET.get('show_chapter') if 'show_chapter' in request.GET else None,
				'chapters': chapters,
				'chapter_count': len(chapters)})
		else:
			return get_unauthorized_message(request, '/login', 'work-update-unauthorized-error')


def publish_work(request, id):
	data = {'id': id, 'draft': False}
	response = do_patch(f'api/works/{id}/', request, data=data, object_name='Work')
	message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
	messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
	return redirect(f'/works/{id}')


def export_work(request, pk, file_ext):
	file_url = do_get(f'api/works/{pk}/export/', request, params={'extension': file_ext}, object_name='Work')
	process_message(file_url)
	if file_url.response_info.status_code >= 400:
		return redirect(f'/works/{pk}')
	response = FileResponse(open(file_url.response_data['media_url'], 'rb'))
	return response


def publish_chapter(request, work_id, chapter_id):
	data = {'id': chapter_id, 'draft': False}
	response = do_patch(f'api/chapters/{chapter_id}/', request, data=data, object_name='Chapter')
	process_message(request, response)
	return redirect(f'/works/{work_id}')


def publish_work_and_chapters(request, id):
	data = {'id': id, 'draft': False}
	response = do_patch(f'api/works/{id}/publish-full/', request, data=data, object_name='Work And Chapters')
	process_message(request, response)
	return redirect(f'/works/{id}')


def publish_bookmark(request, id):
	data = {'id': id, 'draft': False}
	response = do_patch(f'api/bookmarks/{id}/', request, data=data, object_name='Bookmark')
	process_message(request, response)
	return redirect(f'/bookmarks/{id}')


def new_fingerguns(request, work_id):
	data = {'work': str(work_id), 'user': request.user.username}
	response = do_post(f'api/fingerguns/', request, data=data, object_name='Fingergun')
	process_message(request, response)
	return redirect(f'/works/{work_id}')


def delete_work(request, work_id):
	response = do_delete(f'api/works/{work_id}/', request, object_name='Work')
	process_message(request, response)
	return referrer_redirect(request)


def delete_chapter(request, work_id, chapter_id):
	response = do_delete(f'api/chapters/{chapter_id}/', request, object_name='Chapter')
	process_message(request, response)
	return redirect(f'/works/{work_id}/edit/?show_chapter=true')


def new_bookmark(request, work_id):
	if request.user.is_authenticated and request.method != 'POST':
		bookmark = {'title': '', 'description': '', 'user': request.user.username, 'work': {'title': request.GET.get('title'), 'id': work_id}, 'is_private': True}
		bookmark_attributes = do_get(f'api/attributetypes', request, params={'allow_on_bookmark': True}, object_name='Attribute')
		bookmark['attribute_types'] = process_attributes([], bookmark_attributes.response_data['results'])
		tag_types = do_get(f'api/tagtypes', request, 'Tag Type').response_data
		tags = {result['label']:[] for result in tag_types['results']}
		# todo - this should be a specific endpoint, we don't need to retrieve 10 objects to get config
		star_count = do_get(f'api/bookmarks', request, 'Bookmark').response_data['star_count']
		bookmark['rating'] = star_count
		return render(request, 'bookmark_form.html', {
			'tags': tags,
			'rating_range': star_count,
			'form_title': 'New Bookmark',
			'bookmark': bookmark})
	elif request.user.is_authenticated:
		bookmark_dict = get_bookmark_obj(request)
		if len(bookmark_dict['rating']) > 1:
			bookmark_dict['rating'] = 0
		response = do_post(f'api/bookmarks/', request, data=bookmark_dict, object_name='Bookmark')
		process_message(request, response)
		return redirect(f'/bookmarks/{response.response_data["id"]}')
	else:
		return get_unauthorized_message(request, '/login', 'bookmark-create-login-error')


def edit_bookmark(request, pk):
	if request.method == 'POST':
		bookmark_dict = get_bookmark_obj(request)
		response = do_patch(f'api/bookmarks/{pk}/', request, data=bookmark_dict, object_name='Bookmark')
		process_message(request, response)
		return redirect(f'/bookmarks/{pk}')
	else:
		if request.user.is_authenticated:
			tag_types = do_get(f'api/tagtypes', request, 'Tag Type').response_data
			bookmark = do_get(f'api/bookmarks/{pk}/draft', request, 'Bookmark').response_data
			bookmark['description'] = sanitize_rich_text(bookmark['description'])
			bookmark_attributes = do_get(f'api/attributetypes', request, params={'allow_on_bookmark': True}, object_name='Attribute')
			bookmark['attribute_types'] = process_attributes(bookmark['attributes'], bookmark_attributes.response_data['results'])
			tags = group_tags_for_edit(bookmark['tags'], tag_types) if 'tags' in bookmark else []
			return render(request, 'bookmark_form.html', {
				'rating_range': bookmark['star_count'],
				'form_title': 'Edit Bookmark',
				'bookmark': bookmark,
				'tags': tags})
		else:
			return get_unauthorized_message(request, '/login', 'bookmark-update-login-error')


def delete_bookmark(request, bookmark_id):
	response = do_delete(f'api/bookmarks/{bookmark_id}/', request, 'Bookmark')
	process_message(request, response)
	if str(bookmark_id) in request.META.get('HTTP_REFERER'):
		return redirect('/bookmarks')
	return referrer_redirect(request)


def bookmark_collections(request):
	response = do_get(f'api/bookmarkcollections/', request, 'Bookmark Collection').response_data
	bookmark_collections = response['results']
	bookmark_collections = get_object_tags(bookmark_collections)
	for bkcol in bookmark_collections:
		bkcol['attributes'] = get_attributes_for_display(bkcol['attributes'])
	return render(request, 'bookmark_collections.html', {
		'bookmark_collections': bookmark_collections,
		'next': f"/bookmarkcollections/{response['next_params']}" if response['next_params'] is not None else None,
		'previous': f"/bookmarkcollections/{response['prev_params']}" if response['prev_params'] is not None else None,
		'root': settings.ROOT_URL})


def new_bookmark_collection(request):
	if request.user.is_authenticated and request.method != 'POST':
		bookmark_collection = {'title': 'New Bookmark Collection', 'description': '', 'user': request.user.username, 'is_private': True, 'is_draft': True}
		bookmark_collection_attributes = do_get(f'api/attributetypes', request, params={'allow_on_bookmark_collection': True}, object_name='Attribute')
		bookmark_collection['attribute_types'] = process_attributes([], bookmark_collection_attributes.response_data['results'])
		tag_types = do_get(f'api/tagtypes', request, 'Tag Type').response_data
		tags = {result['label']:[] for result in tag_types['results']}
		return render(request, 'bookmark_collection_form.html', {
			'tags': tags,
			'form_title': _('New Collection'),
			'bookmark_collection': bookmark_collection})
	elif request.user.is_authenticated:
		collection_dict = get_bookmark_collection_obj(request)
		response = do_post(f'api/bookmarkcollections/', request, data=collection_dict, object_name='Bookmark Collection')
		process_message(request, response)
		return redirect(f'/bookmark-collections/{response.response_data["id"]}')
	else:
		return get_unauthorized_message(request, '/login', 'bookmark-collection-login-error')


def edit_bookmark_collection(request, pk):
	if request.method == 'POST':
		collection_dict = get_bookmark_collection_obj(request)
		response = do_patch(f'api/bookmarkcollections/{pk}/', request, data=collection_dict, object_name='Bookmark Collection')
		process_message(request, response)
		return redirect(f'/bookmark-collections/{pk}')
	else:
		if request.user.is_authenticated:
			tag_types = do_get(f'api/tagtypes', request, 'Tag Type').response_data
			bookmark_collection = do_get(f'api/bookmarkcollections/{pk}/', request).response_data
			bookmark_collection['description'] = sanitize_rich_text(bookmark_collection['description'])
			bookmark_attributes = do_get(f'api/attributetypes', request, params={'allow_on_bookmark_collection': True}, object_name='Attribute')
			bookmark_collection['attribute_types'] = process_attributes(bookmark_collection['attributes'], bookmark_attributes.response_data['results'])
			tags = group_tags_for_edit(bookmark_collection['tags'], tag_types) if 'tags' in bookmark_collection else []
			return render(request, 'bookmark_collection_form.html', {
				'bookmark_collection': bookmark_collection,
				'form_title': 'Edit Bookmark Collection',
				'tags': tags})
		else:
			return get_unauthorized_message(request, '/login', 'bookmark-collection-update-login-error')


def bookmark_collection(request, pk):
	bookmark_collection = do_get(f'api/bookmarkcollections/{pk}', request, 'Bookmark Collection').response_data
	tags = group_tags(bookmark_collection['tags']) if 'tags' in bookmark_collection else {}
	bookmark_collection['tags'] = tags
	bookmark_collection['attributes'] = get_attributes_for_display(bookmark_collection['attributes'])
	comment_offset = request.GET.get('comment_offset') if request.GET.get('comment_offset') else 0
	if 'comment_thread' in request.GET:
		comment_id = request.GET.get('comment_thread')
		comments = do_get(f"api/collectioncomments/{comment_id}", request, 'Bookmark Collection Comments').response_data
		comment_offset = 0
		comments = {'results': [comments], 'count': request.GET.get('comment_count')}
		bookmark_collection['post_action_url'] = f"/bookmark-collections/{pk}/comments/new?offset={comment_offset}&comment_thread={comment_id}"
		bookmark_collection['edit_action_url'] = f"""/bookmark-collections/{pk}/comments/edit?offset={comment_offset}&comment_thread={comment_id}"""
	else:
		comments = do_get(f'api/bookmarkcollections/{pk}/comments?limit=10&offset={comment_offset}', request, 'Bookmark Collection Comments').response_data
		bookmark_collection['post_action_url'] = f"/bookmark-collections/{pk}/comments/new"
		bookmark_collection['edit_action_url'] = f"""/bookmark-collections/{pk}/comments/edit"""
	for bookmark in bookmark_collection['bookmarks_readonly']:
		bookmark['description'] = bookmark['description'].replace('<p>', '<br/>').replace('</p>', '').replace('<br/>', '', 1)
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	scroll_comment_id = request.GET['scrollCommentId'] if'scrollCommentId' in request.GET else None
	user_can_comment = (bookmark_collection['comments_permitted'] and (bookmark_collection['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in bookmark_collection else False
	bookmark_collection['new_action_url'] = f"/bookmark-collections/{pk}/comments/new"
	return render(request, 'bookmark_collection.html', {
		'load_more_base': f"/bookmark-collections/{pk}",
		'view_thread_base': f"/bookmark-collections/{pk}",
		'bkcol': bookmark_collection,
		'comment_offset': comment_offset,
		'scroll_comment_id': scroll_comment_id,
		'expand_comments': expand_comments,
		'user_can_comment': user_can_comment,
		'comments': comments})


def delete_bookmark_collection(request, pk):
	response = do_delete(f'api/bookmarkcollections/{pk}/', request, 'Bookmark Collection')
	process_message(request, response)
	if request.META is not None and 'HTTP_REFERER' in request.META and str(pk) in request.META.get('HTTP_REFERER'):
		return redirect('/bookmark-collections')
	return referrer_redirect(request)


def publish_bookmark_collection(request, pk):
	data = {'id': pk, 'draft': False}
	response = do_patch(f'api/bookmarkcollections/{pk}/', request, data=data, object_name='Bookmark Collection')
	process_message(request, response)
	return redirect(f'/bookmark-collections/{pk}')


def log_in(request):
	if request.method == 'POST':
		user = authenticate(username=request.POST.get('username').lower(), password=request.POST.get('password'))
		if user is not None:
			login(request, user)
			messages.add_message(request, messages.SUCCESS, _('Login successful.'), 'login-success')
			return referrer_redirect(request, request.POST.get('referrer'))
		else:
			messages.add_message(request, messages.ERROR, _('Login unsuccessful. Please try again.'), 'login-unsuccessful-error')
			return redirect('/login')
	else:
		if 'HTTP_REFERER' in request.META:
			return render(request, 'login.html', {'referrer': request.META['HTTP_REFERER']})
		else:
			return render(request, 'login.html', {'referrer': '/'})


def reset_password(request):
	if request.method == 'POST':
		user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
		if user is not None:
			login(request, user)
			messages.add_message(request, messages.SUCCESS, _('Reset successful.'), 'reset-login-success')
			return referrer_redirect(request)
		else:
			messages.add_message(request, messages.ERROR, _('Reset unsuccessful. Please try again.'), 'reset-login-error')
			return redirect('/login')
	else:
		if 'HTTP_REFERER' in request.META:
			return render(request, 'login.html', {
				'referrer': request.META['HTTP_REFERER']})
		else:
			return render(request, 'login.html', {
				'referrer': '/'})


def register(request):
	if request.method == 'POST':
		response = do_post(f'api/users/', request, data=request.POST, object_name='Registration')
		if response.response_info.status_code >= 200 and response.response_info.status_code < 400:
			messages.add_message(request, messages.SUCCESS, _('Registration successful!'), 'register-success')
			return redirect('/login')
		elif response.response_info.status_code == 403:
			messages.add_message(request, messages.ERROR, _('Registration is not permitted at this time. Please contact site admin.'), 'register-disabled-error')
			return redirect('/')
		else:
			messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
			return redirect('/register')
	else:
		if 'invite_token' in request.GET:
			response = do_get(f'api/invitations/', request, params={'email': request.GET.get('email'), 'invite_token': request.GET.get('invite_token')}, object_name='Invite Code')
			if response.response_info.status_code == 200:
				return render(request, 'register.html', {'permit_registration': True, 'invite_code': response.response_data['invitation']})
			else:
				messages.add_message(request, messages.ERROR, _('Your invite code or email is incorrect. Please check your link again and contact site admin.'), 'register-invalid-token-error')
				return redirect('/')
		permit_registration = do_get(f'api/settings/', request, params={'setting_name': 'Registration Permitted'}, object_name='Setting').response_data
		invite_only = do_get(f'api/settings', request, params={'setting_name': 'Invite Only'}, object_name='Setting').response_data
		if not utils.convert_boolean(permit_registration['results'][0]['value']):
			return render(request, 'register.html', {'permit_registration': False})
		elif utils.convert_boolean(invite_only['results'][0]['value']):
			return redirect('/request-invite')
		else:
			return render(request, 'register.html', {
				'permit_registration': True,
				'username_check_url': 'registration-utils'
			})


def request_invite(request):
	if request.method == 'POST':
		response = do_post(f'api/invitations/', request, data=request.POST.copy(), object_name='Invitation')
		if response.response_info.status_code >= 200 and response.response_info.status_code < 400:
			messages.add_message(request, messages.SUCCESS, _('You have been added to the invite queue.'), 'invite-request-success')
			return render(request, 'request_invite.html', {'invite_sent': True})
		elif response.response_info.status_code == 403:
			messages.add_message(request, messages.ERROR, _('An error occurred requesting your invite. Please contact site admin.'), 'invite-request-error')
			return redirect('/')
		elif response.response_info.status_code == 418:
			messages.add_message(request, messages.ERROR, _('Your account already exists. Please log in or reset your password.'), 'invite-request-dupe-error')
			return redirect('/login')
	else:
		return render(request, 'request_invite.html', {'invite_sent': False})


def log_out(request):
	logout(request)
	messages.add_message(request, messages.SUCCESS, _('Logout successful.'), 'logout-success')
	return redirect(request.META['HTTP_REFERER'])


@require_http_methods(["GET"])
def work(request, pk, chapter_offset=0):
	view_full = request.GET.get('view_full', False)
	work_types = do_get(f'api/worktypes', request, 'Work Type').response_data
	url = f'api/works/{pk}/'
	work_response = do_get(url, request, 'Work')
	if work_response.response_info.status_code >= 400:
		messages.add_message(request, messages.ERROR, work_response.response_info.message, work_response.response_info.type_label)
		return redirect('/')
	work = work_response.response_data
	tags = group_tags(work['tags']) if 'tags' in work else {}
	work['attributes'] = get_attributes_for_display(work['attributes'])
	chapter_url_string = f'api/works/{pk}/chapters{"?limit=1" if view_full is False else "/all"}'
	if chapter_offset > 0:
		chapter_url_string = f'{chapter_url_string}&offset={chapter_offset}'
	chapter_response = do_get(chapter_url_string, request, 'Chapter').response_data
	chapter_json = chapter_response['results'] if 'results' in chapter_response else chapter_response
	user_can_comment = (work['comments_permitted'] and (work['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in work else False
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	chapters = []
	for chapter in chapter_json:
		chapter['updated_on'] = parse(chapter['updated_on']).date()
		if 'id' in chapter:
			if 'comment_thread' not in request.GET:
				comment_offset = request.GET.get('comment_offset') if request.GET.get('comment_offset') else 0
				chapter_comments = do_get(f"api/chapters/{chapter['id']}/comments?limit=10&offset={comment_offset}", request, "Chapter Comments").response_data
				chapter['post_action_url'] = f"/works/{pk}/chapters/{chapter['id']}/comments/new?offset={chapter_offset}"
				chapter['edit_action_url'] = f"""/works/{pk}/chapters/{chapter['id']}/comments/edit?offset={chapter_offset}"""
			else:
				comment_id = request.GET.get('comment_thread')
				chapter_comments = do_get(f"api/comments/{comment_id}", request, 'Chapter Comments').response_data
				comment_offset = 0
				chapter_comments = {'results': [chapter_comments], 'count': request.GET.get('comment_count')}
				chapter['post_action_url'] = f"/works/{pk}/chapters/{chapter['id']}/comments/new?offset={chapter_offset}&comment_thread={comment_id}"
				chapter['edit_action_url'] = f"""/works/{pk}/chapters/{chapter['id']}/comments/edit?offset={chapter_offset}&comment_thread={comment_id}"""
			chapter['comments'] = chapter_comments
			chapter['comment_offset'] = comment_offset
			chapter['load_more_base'] = f"/works/{pk}/chapters/{chapter['id']}/{chapter_offset}"
			chapter['view_thread_base'] = f"/works/{pk}/{chapter_offset}"
			chapter['attributes'] = get_attributes_for_display(chapter['attributes'])
			chapter['new_action_url'] = f"/works/{pk}/chapters/{chapter['id']}/comments/new?offset={chapter_offset}"
			chapters.append(chapter)
	return render(request, 'work.html', {
		'work_types': work_types['results'],
		'work': work,
		'user_can_comment': user_can_comment,
		'expand_comments': expand_comments,
		'scroll_comment_id': request.GET.get("scrollCommentId") if request.GET.get("scrollCommentId") is not None else None,
		'id': pk,
		'tags': tags,
		'view_full': view_full,
		'root': settings.ROOT_URL,
		'chapters': chapters,
		'chapter_offset': chapter_offset,
		'next_chapter': f'/works/{pk}/{chapter_offset + 1}' if 'next' in chapter_response and chapter_response['next'] else None,
		'previous_chapter': f'/works/{pk}/{chapter_offset - 1}' if 'previous' in chapter_response and chapter_response['previous'] else None,})


def render_comments_common(request, get_comment_base, object_name, object_id, load_more_base, view_thread_base,
		delete_obj, post_action_url, edit_action_url, root_obj_id=None, additional_params={}):
	limit = request.GET.get('limit', '')
	offset = request.GET.get('offset', '')
	depth = request.GET.get('depth', 0)
	comments = do_get(f'{get_comment_base}/comments?limit={limit}&offset={offset}', request, 'Comments').response_data
	response_dict = {
		'comments': comments['results'],
		'current_offset': comments['current'],
		'top_level': 'true',
		'depth': int(depth),
		object_name: {'id': object_id},
		'load_more_base': load_more_base,
		'comment_count': comments['count'],
		'view_thread_base': view_thread_base,
		'delete_obj': delete_obj,
		'object_name': object_name,
		'object': {'id': object_id},
		'next_params': comments['next_params'],
		'prev_params': comments['prev_params'],
		'post_action_url': post_action_url,
		'edit_action_url': edit_action_url
	}
	if root_obj_id:
		response_dict['root_obj_id'] = root_obj_id
	response_dict = response_dict | additional_params
	return render(request, 'comments.html', response_dict)


def render_chapter_comments(request, work_id, chapter_id, chapter_offset):
	post_action_url = f"/works/{work_id}/chapters/{chapter_id}/comments/new?offset={chapter_offset}"
	edit_action_url = f"""/works/{work_id}/chapters/{chapter_id}/comments/edit?offset={chapter_offset}"""
	get_comment_base = f'api/chapters/{chapter_id}'
	view_thread_base = f"/works/{work_id}/{chapter_offset}"
	load_more_base = f"/works/{work_id}/chapters/{chapter_id}/{chapter_offset}"
	return render_comments_common(
		request, get_comment_base, 'chapter', chapter_id, load_more_base, view_thread_base,
		'chapter-comment', post_action_url, edit_action_url, work_id, {'chapter-offset': chapter_offset})


def render_collection_comments(request, pk):
	post_action_url = f'/bookmark-collections/{pk}/comments/new'
	edit_action_url = f'/bookmark-collections/{pk}/comments/edit'
	get_comment_base = f'api/bookmarkcollections/{pk}'
	common_base = f'/bookmark-collections/{pk}'
	return render_comments_common(
		request, get_comment_base, 'collection', pk, common_base, common_base,
		'collection-comment', post_action_url, edit_action_url)


def render_bookmark_comments(request, pk):
	common_base = f"/bookmarks/{pk}"
	get_comment_base = f'api/bookmarks/{pk}'
	post_action_url = f'/bookmarks/{pk}/comments/new'
	edit_action_url = f'/bookmarks/{pk}/comments/edit'
	return render_comments_common(
		request, get_comment_base, 'bookmark', pk, common_base, common_base,
		'bookmark-comment', post_action_url, edit_action_url)


def create_comment_common(request, captcha_fail_redirect, object_name, redirect_url, redirect_url_threaded):
	if not request.method == 'POST':
		return None
	if not request.user.is_authenticated:
		if settings.USE_CAPTCHA:
			captcha_passed = validate_captcha(request)
			if not captcha_passed:
				messages.add_message(request, messages.ERROR, 'Captcha failed. Please try again.', 'captcha-fail-error')
				return redirect(captcha_fail_redirect)
	comment_dict = request.POST.copy()
	comment_count = int(request.POST.get(f'{object_name}_comment_count'))
	comment_thread = int(request.GET.get('comment_thread')) if 'comment_thread' in request.GET else None
	if comment_count > 10 and request.POST.get('parent_comment') is None:
		comment_offset = int(int(request.POST.get(f'{object_name}_comment_count')) / 10) * 10
	elif comment_count > 10 and request.POST.get('parent_comment') is not None:
		comment_offset = request.POST.get('parent_comment_next')
	else:
		comment_offset = 0
	if request.user.is_authenticated:
		comment_dict["user"] = str(request.user)
	else:
		comment_dict["user"] = None
	response = do_post(f'api/{object_name}comments/', request, data=comment_dict, object_name='Comment')
	comment_id = response.response_data['id'] if 'id' in response.response_data else None
	redirect_url = f'{redirect_url}expandComments=true&scrollCommentId={comment_id}&comment_offset={comment_offset}'
	redirect_url_threaded = f'{redirect_url_threaded}expandComments=true&scrollCommentId={comment_id}&comment_thread={comment_thread}&comment_count={comment_count}'
	process_message(request, response)
	if comment_thread is None:
		return redirect(redirect_url)
	else:
		return redirect(redirect_url_threaded)


def edit_comment_common(request, object_name, error_redirect, redirect_url, redirect_url_threaded):
	if not request.method == 'POST':
		messages.add_message(request, messages.ERROR, _('Invalid URL.'), f'{object_name}-comment-edit-not-found')
		return redirect(error_redirect)
	comment_dict = request.POST.copy()
	comment_count = int(request.POST.get(f'{object_name}_comment_count'))
	comment_thread = int(request.GET.get('comment_thread')) if 'comment_thread' in request.GET else None
	if comment_count > 10 and request.POST.get('parent_comment_val') is None:
		comment_offset = int(int(request.POST.get(f'{object_name}_comment_count')) / 10) * 10
	elif comment_count > 10 and request.POST.get('parent_comment_val') is not None:
		comment_offset = request.POST.get('parent_comment_next')
	else:
		comment_offset = 0
	comment_dict.pop('parent_comment_val')
	if request.user.is_authenticated:
		comment_dict["user"] = str(request.user)
	else:
		comment_dict["user"] = None
	response = do_patch(f"api/{object_name}comments/{comment_dict['id']}/", request, data=comment_dict, object_name='Comment')
	process_message(request, response)
	redirect_url = f'{redirect_url}expandComments=true&scrollCommentId={comment_dict["id"]}&comment_offset={comment_offset}'
	if comment_thread is None:
		return redirect(redirect_url)
	else:
		redirect_url_threaded = f'{redirect_url_threaded}expandComments=true&scrollCommentId={comment_dict["id"]}&comment_thread={comment_thread}&comment_count={comment_count}'
		return redirect(redirect_url_threaded)


def delete_comment_common(request, redirect_url, object_name, comment_id):
	response = do_delete(f'api/{object_name}comments/{comment_id}/', request, 'Comment')
	process_message(request, response)
	return redirect(redirect_url)


def create_chapter_comment(request, work_id, chapter_id):
	captcha_redirect_url = f'/works/{work_id}/'
	object_name = 'chapter'
	redirect_url = f'/works/{work_id}/{int(request.GET.get("offset", 0))}?'
	return create_comment_common(request, captcha_redirect_url, object_name, redirect_url, redirect_url)


def edit_chapter_comment(request, work_id, chapter_id):
	object_name = 'chapter'
	redirect_url = f'/works/{work_id}/{int(request.GET.get("offset", 0))}?'
	error_redirect = f'/works/{work_id}'
	return edit_comment_common(request, object_name, error_redirect, redirect_url, redirect_url)


def delete_chapter_comment(request, work_id, chapter_id, comment_id):
	return delete_comment_common(request, f'/works/{work_id}/chapters/{chapter_id}', 'chapter', comment_id)


def create_bookmark_comment(request, pk):
	captcha_redirect_url = f'/bookmarks/{pk}/'
	object_name = 'bookmark'
	redirect_url = f'/bookmarks/{pk}/?'
	return create_comment_common(request, captcha_redirect_url, object_name, redirect_url, redirect_url)


def edit_bookmark_comment(request, pk):
	object_name = 'bookmark'
	error_redirect = f'/bookmarks/{pk}'
	redirect_url = f'/bookmarks/{pk}/?'
	return edit_comment_common(request, object_name, error_redirect, redirect_url, redirect_url)


def delete_bookmark_comment(request, pk, comment_id):
	return delete_comment_common(request, f'/bookmarks/{pk}', 'bookmark', comment_id)


def create_collection_comment(request, pk):
	captcha_redirect_url = f'/bookmark-collections/{pk}/'
	object_name = 'collection'
	redirect_url = f'/bookmark-collections/{pk}/?'
	return create_comment_common(request, captcha_redirect_url, object_name, redirect_url, redirect_url)


def edit_collection_comment(request, pk):
	object_name = 'collection'
	error_redirect = f'/bookmark-collections/{pk}'
	redirect_url = f'/bookmark-collections/{pk}/?'
	return edit_comment_common(request, object_name, error_redirect, redirect_url, redirect_url)


def delete_collection_comment(request, pk, comment_id):
	return delete_comment_common(request, f'/bookmark-collections/{pk}', 'collection', comment_id)


def bookmarks(request):
	response = do_get(f'api/bookmarks/', request, params=request.GET, object_name='Bookmark').response_data
	bookmarks = response['results'] if 'results' in response else []
	previous_param = response['prev_params']
	next_param = response['next_params']
	bookmarks = get_object_tags(bookmarks)
	for bookmark in bookmarks:
		bookmark['attributes'] = get_attributes_for_display(bookmark['attributes'])
	return render(request, 'bookmarks.html', {
		'bookmarks': bookmarks,
		'rating_range': response['star_count'],
		'next': f"/bookmarks/{next_param}" if next_param is not None else None,
		'previous': f"/bookmarks/{previous_param}" if previous_param is not None else None})


def bookmark(request, pk):
	bookmark = do_get(f'api/bookmarks/{pk}', request, 'Bookmark').response_data
	tags = group_tags(bookmark['tags']) if 'tags' in bookmark else {}
	bookmark['attributes'] = get_attributes_for_display(bookmark['attributes']) if 'attributes' in bookmark else {}
	comment_offset = request.GET.get('comment_offset') if request.GET.get('comment_offset') else 0
	if 'comment_thread' in request.GET:
		comment_id = request.GET.get('comment_thread')
		comments = do_get(f"api/bookmarkcomments/{comment_id}", request, 'Bookmark Comments').response_data
		comment_offset = 0
		comments = {'results': [comments], 'count': request.GET.get('comment_count')}
		bookmark['post_action_url'] = f"/bookmarks/{pk}/comments/new?offset={comment_offset}&comment_thread={comment_id}"
		bookmark['edit_action_url'] = f"""/bookmarks/{pk}/comments/edit?offset={comment_offset}&comment_thread={comment_id}"""
	else:
		comments = do_get(f'api/bookmarks/{pk}/comments?limit=10&offset={comment_offset}', request, 'Bookmark Comment').response_data
		bookmark['post_action_url'] = f"/bookmarks/{pk}/comments/new"
		bookmark['edit_action_url'] = f"""/bookmarks/{pk}/comments/edit"""
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	bookmark['new_action_url'] = f"/bookmarks/{pk}/comments/new"
	scroll_comment_id = request.GET['scrollCommentId'] if'scrollCommentId' in request.GET else None
	user_can_comment = (bookmark['comments_permitted'] and (bookmark['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in bookmark else False
	return render(request, 'bookmark.html', {
		'bookmark': bookmark,
		'load_more_base': f"/bookmarks/{pk}",
		'view_thread_base': f"/bookmarks/{pk}",
		'tags': tags,
		'comment_offset': comment_offset,
		'scroll_comment_id': scroll_comment_id,
		'expand_comments': expand_comments,
		'user_can_comment': user_can_comment,
		'rating_range': bookmark['star_count'] if 'star_count' in bookmark else [],
		'work': bookmark['work'] if 'work' in bookmark else {},
		'comments': comments})


def works_by_tag(request, tag):
	return search(request)


def works_by_tag_next(request, tag_id):
	if 'next' in request.GET:
		next_url = request.GET.get('next', '')
	else:
		next_url = request.GET.get('previous', '')
	offset_url = request.GET.get('offset', '')
	works = do_get(f'{next_url}&offset={offset_url}', request, 'Work').response_data
	return render(request, 'paginated_works.html', {'works': works, 'tag_id': tag_id})


@never_cache
def switch_css_mode(request):
	request.session['css_mode'] = "dark" if request.session.get('css_mode') == "light" or request.session.get('css_mode') is None else "light"
	from django.core.cache import cache
	# TODO: this is awful, should be clearing the cache per-user and only for frontend stuff
	cache.clear()
	return HttpResponse("OK")
