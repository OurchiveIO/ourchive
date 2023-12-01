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
from dateutil import tz
from urllib.parse import unquote, quote
import random
from django.core.cache import cache
from django.views.decorators.vary import vary_on_cookie
from operator import itemgetter
from .searcher import build_and_execute_search
from .view_utils import *

logger = logging.getLogger(__name__)

def index(request):
	top_tags = []
	recent_works = []
	response = do_get(f'api/tags/top', request, params=request.GET, object_name='top tags')
	if response.response_info.status_code >= 200 and response.response_info.status_code < 300:
		top_tags = response.response_data['results']
		top_tags = sorted(top_tags, key=itemgetter('tag_count'), reverse=True)
		highest_count = top_tags[0]['tag_count']
		tag_max_size = 3
		for tag in top_tags:
			tag_count = tag['tag_count']
			font_size = tag_count / highest_count * tag_max_size
			font_size = abs(float(font_size))
			if (font_size <= 1):
				font_size = font_size + 1
			tag['font_size'] = f'{font_size}em'
		random.shuffle(top_tags)
	response = do_get(f'api/works/recent', request, params=request.GET, object_name='recent works')
	if response.response_info.status_code >= 200 and response.response_info.status_code < 300:
		recent_works = response.response_data['results']
	return render(request, 'index.html', {
		'heading_message': _('ourchive_welcome'),
		'long_message': _('ourchive_intro_copy'),
		'root': settings.ROOT_URL,
		'top_tags': top_tags,
		'recent_works': recent_works,
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


def user_name(request, pk):
	user = do_get(f"api/users/profile/{pk}", request, params=request.GET, object_name='User')
	user_blocked = False
	if request.user.is_authenticated:
		response = do_get(f'api/userblocks/blocked/{pk}', request, 'user block')
		if response.response_data['user_blocked']:
			user_blocked = response.response_data['block_id']
	if user.response_info.status_code >= 400:
		messages.add_message(request, messages.ERROR, user.response_info.message, user.response_info.type_label)
		return redirect('/')
	username = user.response_data['results'][0]['username']
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
	works = format_date_for_template(works, 'updated_on', True)
	work_next = f'/username/{pk}/{works_response.response_data["next_params"].replace("limit=", "work_limit=").replace("offset=", "work_offset=")}' if works_response.response_data["next_params"] is not None else None
	work_previous = f'/username/{pk}/{works_response.response_data["prev_params"].replace("limit=", "work_limit=").replace("offset=", "work_offset=")}' if works_response.response_data["prev_params"] is not None else None
	bookmarks_response = do_get(f'api/users/{username}/bookmarks', request, params=bookmark_params).response_data
	bookmarks = bookmarks_response['results']
	bookmark_next = f'/username/{pk}/{bookmarks_response["next_params"].replace("limit=", "bookmark_limit=").replace("offset=", "bookmark_offset=")}' if bookmarks_response["next_params"] is not None else None
	bookmark_previous = f'/username/{pk}/{bookmarks_response["prev_params"].replace("limit=", "bookmark_limit=").replace("offset=", "bookmark_offset=")}' if bookmarks_response["prev_params"] is not None else None
	bookmarks = get_object_tags(bookmarks)
	bookmarks = format_date_for_template(bookmarks, 'updated_on', True)
	bookmark_collection_response = do_get(f'api/users/{username}/bookmarkcollections', request, params=bookmark_collection_params).response_data
	bookmark_collection = bookmark_collection_response['results']
	bookmark_collection_next = f'/username/{pk}/{bookmark_collection_response["next_params"].replace("limit=", "bookmark_collection_limit=").replace("offset=", "bookmark_collection_offset=")}' if bookmark_collection_response["next_params"] is not None else None
	bookmark_collection_previous = f'/username/{pk}/{bookmark_collection_response["prev_params"].replace("limit=", "bookmark_collection_limit=").replace("offset=", "bookmark_collection_offset=")}' if bookmark_collection_response["prev_params"] is not None else None
	bookmark_collection = get_object_tags(bookmark_collection)
	bookmark_collection = format_date_for_template(bookmark_collection, 'updated_on', True)
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
		'user_blocked': user_blocked,
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
		return redirect('/login')
	if request.method == 'POST':
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
		return redirect('/')
	return render(request, 'work_import_form.html', {
		'form_title': _('Import AO3 Work(s)'),
		'referer': request.META.get('HTTP_REFERER')
		})


def import_works_status(request, pk):
	if not request.user.is_authenticated:
		messages.add_message(request, messages.ERROR, _('You must be logged in to import works.'), 'Import')
		return redirect('/login')
	user_imports = do_get(f'api/users/{pk}/importstatus', request, params=request.GET, object_name='Imports')
	for job in user_imports.response_data['results']:
		job['created_on'] = parse(job['created_on'])
	return render(request, 'user_import_status.html', {
		'page_title': _('Pending Imports'),
		'user_imports': user_imports.response_data
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


def block_user(request, pk):
	data = {'user': request.user.username, 'blocked_user': pk}
	blocklist = do_post(f'api/userblocks', request, data, 'Block')
	message_type = messages.WARNING
	if blocklist.response_info.status_code >= 400:
		message_type = messages.ERROR
	elif blocklist.response_info.status_code >= 200:
		message_type = messages.SUCCESS
	messages.add_message(request, message_type, blocklist.response_info.message, blocklist.response_info.type_label)
	return redirect(f'/username/{pk}')


def unblock_user(request, user_id, pk):
	blocklist = do_delete(f'api/userblocks/{pk}', request, 'Blocklist')
	message_type = messages.WARNING
	if blocklist.response_info.status_code >= 400:
		message_type = messages.ERROR
	elif blocklist.response_info.status_code >= 200:
		message_type = messages.SUCCESS
	messages.add_message(request, message_type, _('User unblocked.'), blocklist.response_info.type_label)
	if 'HTTP_REFERER' in request.META and 'username' in request.META.get('HTTP_REFERER'):
		return referrer_redirect(request)
	return redirect(f'/users/{request.user.username}/blocklist')


def report_user(request, username):
	if request.method == 'POST':
		report_data = request.POST.copy()
		# we don't want to let the user specify this
		report_data['user'] = request.user.username
		response = do_post(f'api/userreports/', request, data=report_data, object_name='User Report')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		return redirect(f'/')
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
	response = get_works_list(request, username)
	next_params = response['next_params']
	prev_params = response['prev_params']
	works = response['works']
	works = format_date_for_template(works, 'updated_on', True)
	return render(request, 'works.html', {
		'works': works,
		'next': f"/username/{username}/works/{next_params}" if next_params is not None else None,
		'previous': f"/username/{username}/works/{prev_params}" if prev_params is not None else None,
		'user_filter': username,
		'root': settings.ROOT_URL})


def user_works_drafts(request, username):
	response = do_get(f'api/users/{username}works/drafts', request)
	works = response.response_data['results']
	works = get_object_tags(works)
	works = format_date_for_template(works, 'updated_on', True)
	return render(request, 'works.html', {
		'works': works,
		'user_filter': username,
		'root': settings.ROOT_URL})


def edit_account(request, pk):
	if request.method == 'POST':
		user_data = request.POST.copy()
		profile_id = user_data['id']
		user_data.pop('id')
		response = do_patch(f'api/users/{profile_id}/', request, data=user_data, object_name='Account')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		return redirect('/username/{pk}')
	else:
		if request.user.is_authenticated:
			response = do_get(f"api/users/profile/{pk}", request)
			user = response.response_data['results']
			if len(user) > 0:
				user = user[0]
				return render(request, 'account_form.html', {'user': user})
			else:
				messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
				return redirect(f'/username/{pk}')
		else:
			messages.add_message(request, messages.ERROR, _('You must log in as this user to perform this action.'), 'user-info-unauthorized-error')
			return redirect('/login')


def edit_user(request, pk):
	if request.method == 'POST':
		user_data = request.POST.copy()
		if 'icon' not in user_data or user_data['icon'] == "":
			user_data['icon'] = user_data['unaltered_icon']
		user_data.pop('unaltered_icon')
		user_id = user_data.pop('user_id')[0]
		user_data['collapse_chapter_image'] = 'collapse_chapter_image' in user_data
		user_data['collapse_chapter_audio'] = 'collapse_chapter_audio' in user_data
		user_data['collapse_chapter_text'] = 'collapse_chapter_text' in user_data
		user_data["attributes"] = get_attributes_from_form_data(request)
		response = do_patch(f'api/users/{user_id}/', request, data=user_data, object_name='User Profile')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		return redirect(f'/username/{pk}/')
	else:
		if request.user.is_authenticated:
			work_types = do_get(f'api/worktypes', request, 'Work').response_data['results']
			response = do_get(f"api/users/profile/{request.user.id}", request, 'User Profile')
			if response.response_info.status_code >= 400:
				messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
				return redirect(f'/username/{pk}')
			user = response.response_data['results']
			user = user[0]
			if user is not None:
				user['profile'] = sanitize_rich_text(user['profile'])
			user_attributes = do_get(f'api/attributetypes', request, params={'allow_on_user': True}, object_name='Attribute')
			user['attribute_types'] = process_attributes(user['attributes'], user_attributes.response_data['results'])
			return render(request, 'user_form.html', {
				'user': user, 'form_title': 'Edit User',
				'work_types': work_types,
				})
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
	bookmarks = format_date_for_template(bookmarks, 'updated_on', True)
	return render(request, 'bookmarks.html', {
		'bookmarks': bookmarks,
		'rating_range': response.response_data['star_count'],
		'next': f"/username/{username}/bookmarks/{response.response_data['next_params']}" if response.response_data["next_params"] is not None else None,
		'previous': f"/username/{username}/bookmarks/{response.response_data['prev_params']}" if response.response_data["prev_params"] is not None else None,
		'user_filter': username})


def user_bookmark_collections(request, username):
	response = do_get(f'api/users/{username}/bookmarkcollections', request, params=request.GET, object_name='Bookmark Collections')
	bookmark_collections = response.response_data['results']
	bookmark_collections = get_object_tags(bookmark_collections)
	bookmark_collections = format_date_for_template(bookmark_collections, 'updated_on', True)
	return render(request, 'bookmark_collections.html', {
		'bookmark_collections': bookmark_collections,
		'next': f"/username/{username}/bookmarkcollections/{response.response_data['next_params']}" if response.response_data["next_params"] is not None else None,
		'previous': f"/username/{username}/bookmarkcollections/{response.response_data['prev_params']}" if response.response_data["prev_params"] is not None else None,
		'user_filter': username})


def user_notifications(request, username):
	if not request.user.is_authenticated or not request.user.username == username:
		messages.add_message(request, messages.ERROR, _('You do not have permission to view these notifications.'), 'notification-not-authed')
		return redirect('/')
	response = do_get(f'api/users/{username}/notifications', request, params=request.GET, object_name='Notification')
	if response.response_info.status_code == 204 or response.response_info.status_code == 200:
		notifications = response.response_data['results']
		return render(request, 'notifications.html', {
			'notifications': notifications,
			'page_title': _('Notifications'),
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

def user_notifications_all_read(request, username):
	data = {'user': username}
	response = do_patch(f'api/notifications/read/', request, data, object_name='Notification')
	message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
	messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
	return redirect(f'/username/{username}/notifications')

def user_bookmarks_drafts(request, username):
	response = do_get(f'api/users/{username}/bookmarks/drafts', request, 'User Bookmarks')
	bookmarks = response.response_data['results']
	bookmarks = get_object_tags(bookmarks)
	return render(request, 'bookmarks.html', {'bookmarks': bookmarks, 'user_filter': username})


def user_bookmark_subscriptions(request, username):
	if not request.user.is_authenticated or not request.user.username == username:
		messages.add_message(request, messages.ERROR, _('You do not have permission to view these subscriptions.'), 'subscription-not-authed')
		return redirect('/')
	cache_key = f'subscription_{username}_{request.user}_bookmarks'
	if cache.get(cache_key):
		return cache.get(cache_key)
	response = do_get(f'api/users/{username}/subscriptions/bookmarks', request)
	page_content = render(request, 'user_bookmark_subscriptions.html', {
		'bookmarks': response.response_data
	})
	if not cache.get(cache_key) and len(messages.get_messages(request)) < 1:
		cache.set(cache_key, page_content, 60 * 60)
	return page_content


def user_collection_subscriptions(request, username):
	if not request.user.is_authenticated or not request.user.username == username:
		messages.add_message(request, messages.ERROR, _('You do not have permission to view these subscriptions.'), 'subscription-not-authed')
		return redirect('/')
	cache_key = f'subscription_{username}_{request.user}_collections'
	if cache.get(cache_key):
		return cache.get(cache_key)
	response = do_get(f'api/users/{username}/subscriptions/collections', request, params=request.GET)
	page_content = render(request, 'user_collection_subscriptions.html', {
		'bookmark_collections': response.response_data,
		'next': f"/users/{username}/subscriptions/collections/{response.response_data['next_params']}" if response.response_data['next_params'] is not None else None,
		'previous': f"/users/{username}/subscriptions/collections/{response.response_data['prev_params']}" if response.response_data['prev_params'] is not None else None,
	})
	if not cache.get(cache_key) and len(messages.get_messages(request)) < 1:
		cache.set(cache_key, page_content, 60 * 60)
	return page_content


def user_subscriptions(request, username):
	if not request.user.is_authenticated or not request.user.username == username:
		messages.add_message(request, messages.ERROR, _('You do not have permission to view these subscriptions.'), 'subscription-not-authed')
		return redirect('/')
	cache_key = f'subscription_{username}_{request.user}'
	if cache.get(cache_key):
		return cache.get(cache_key)
	response = do_get(f'api/users/{username}/subscriptions', request, 'Subscription')
	page_content = render(request, 'user_subscriptions.html', {
		'subscriptions': response.response_data['results'] if 'results' in response.response_data else {}
	})
	if not cache.get(cache_key) and len(messages.get_messages(request)) < 1:
		cache.set(cache_key, page_content, 60 * 60)
	return page_content


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


def search(request):
	template_data = build_and_execute_search(request)
	if not template_data:
		return redirect('/')
	return render(request, 'search_results.html', template_data)


def search_filter(request):
	template_data = build_and_execute_search(request)
	if not template_data:
		return redirect('/')
	return render(request, 'search_results.html', template_data)


def tag_autocomplete(request):
	term = request.GET.get('text')
	params = {'term': term}
	params['type'] = request.GET.get('type') if 'type' in request.GET else ''
	params['fetch_all'] = request.GET.get('fetch_all') if 'fetch_all' in request.GET else ''
	response = do_get(f'api/tag-autocomplete', request, params, 'Tag')
	template = 'tag_autocomplete.html' if request.GET.get('source') == 'search' else 'edit_tag_autocomplete.html'
	tags = response.response_data['results']
	for tag in tags:
		tag['display_text_clean'] = tag['display_text'].replace("'", "\\'")
	return render(request, template, {
		'tags': tags,
		'divider': settings.TAG_DIVIDER,
		'fetch_all': params['fetch_all']})


def bookmark_autocomplete(request):
	term = request.GET.get('text')
	params = {'term': term}
	response = do_get(f'api/bookmark-autocomplete', request, params, 'Bookmark')
	bookmarks = response.response_data['results']
	for bookmark in bookmarks:
		bookmark['bookmark']['title_clean'] = bookmark['bookmark']['title'].replace("'", "\\'")
		bookmark['bookmark']['work']['title_clean'] = bookmark['bookmark']['work']['title'].replace("'", "\\'")
	template = 'bookmark_collection_autocomplete.html'
	return render(request, template, {
		'bookmarks': bookmarks})


@require_http_methods(["GET"])
def works(request):
	response = do_get(f'api/works/', request, params=request.GET, object_name='Work')
	works_response = response.response_data
	works = response.response_data['results'] if 'results' in response.response_data else []
	works = get_object_tags(works)
	works = get_array_attributes_for_display(works, 'attributes')
	works = format_date_for_template(works, 'updated_on', True)
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
		work = {
			'title': 'Untitled Work',
			'user': request.user.username,
			'download_choices': [
				('EPUB', 'EPUB'), ('M4B', 'M4B'), ('ZIP', 'ZIP'), ('M4A', 'M4A'),
				('MOBI', 'MOBI')],
			'anon_comments_permitted': True,
			'comments_permitted': True
		}
		work_chapter = {
			'title': '',
			'number': 1
		}
		tag_types = do_get(f'api/tagtypes', request, 'Tag').response_data
		tags = group_tags_for_edit([], tag_types)
		work_attributes = do_get(f'api/attributetypes', request, params={'allow_on_work': True}, object_name='Work Attributes')
		work['attribute_types'] = process_attributes([], work_attributes.response_data['results'])
		return render(request, 'work_form.html', {
			'tags': tags,
			'divider': settings.TAG_DIVIDER,
			'form_title': 'New Work',
			'work_types': work_types['results'],
			'work': work,
			'work_chapter': work_chapter})
	elif request.user.is_authenticated:
		work_data = get_work_obj(request)
		chapter_dict = work_data[3]
		work = do_post(f'api/works/', request, work_data[0], 'Work').response_data
		if chapter_dict:
			chapter_dict['work'] = work['id']
			response = do_post(f'api/chapters/', request, chapter_dict, 'Chapter')
			if response.response_info.status_code >= 400:
				messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
		if work_data[4]:
			data = {'id': id, 'draft': False}
			response = do_patch(f'api/works/{work["id"]}/publish-full/', request, data=data, object_name='Work And Chapters')
		if work_data[1] == 'false' or chapter_dict is not None:
			return redirect(f'/works/{work["id"]}')
		else:
			return redirect(f'/works/{work["id"]}/chapters/new?count=0')
	else:
		messages.add_message(request, messages.ERROR, _('You must log in to post a new work.'), 'new-work-unauthorized-error')
		return redirect('/login')


def new_chapter(request, work_id):
	if request.user.is_authenticated and request.method != 'POST':
		count = request.GET.get('count') if request.GET.get('count') != '' else 0
		chapter = {'title': '', 'work': work_id, 'text': '', 'number': int(count) + 1}
		chapter_attributes = do_get(f'api/attributetypes', request, params={'allow_on_chapter': True}, object_name='Chapter')
		chapter['attribute_types'] = process_attributes([], chapter_attributes.response_data['results'])
		return render(request, 'chapter_form.html', {
			'chapter': chapter,
			'form_title': 'New Chapter'})
	elif request.user.is_authenticated:
		chapter_dict = request.POST.copy()
		chapter_dict["draft"] = "chapter_draft" in chapter_dict
		chapter_dict["attributes"] = get_attributes_from_form_data(request)
		if 'audio_length' in chapter_dict and not chapter_dict['audio_length']:
			chapter_dict['audio_length'] = 0
		response = do_post(f'api/chapters/', request, data=chapter_dict, object_name='Chapter')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		redirect_url = f'/works/{work_id}/?offset={request.GET.get("from_work", 0)}' if 'from_work' in request.GET else f"/works/{work_id}/edit/?multichapter=true#work-form-chapter-content-parent"
		return redirect(redirect_url)
	else:
		messages.add_message(request, messages.ERROR, _('You must log in to post a new chapter.'), 'chapter-create-login-error')
		return redirect('/login')


def edit_chapter(request, work_id, id):
	if request.method == 'POST':
		chapter_dict = request.POST.copy()
		chapter_dict["draft"] = "chapter_draft" in chapter_dict
		chapter_dict["attributes"] = get_attributes_from_form_data(request)
		response = do_patch(f'api/chapters/{id}/', request, data=chapter_dict, object_name='Chapter')
		message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
		messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
		redirect_url = f'/works/{work_id}/?offset={request.GET.get("from_work", 0)}' if 'from_work' in request.GET else f"/works/{work_id}/edit/#work-form-chapter-content-parent"
		return redirect(redirect_url)
	else:
		if request.user.is_authenticated:
			chapter = do_get(f'api/chapters/{id}', request, 'Chapter').response_data
			chapter = prepare_chapter_data(chapter, request)
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
		chapter_dict = work_dict[3]
		response = do_patch(f'api/works/{id}/', request, data=work_dict[0], object_name='Work')
		if response.response_info.status_code == 200:
			messages.add_message(request, messages.SUCCESS, response.response_info.message, response.response_info.type_label)
			if chapter_dict:
				if 'id' in chapter_dict and chapter_dict['id']:
					response = do_patch(f'api/chapters/{chapter_dict["id"]}/', request, chapter_dict, 'Chapter')
				else:
					response = do_post(f'api/chapters/', request, chapter_dict, 'Chapter')
				if response.response_info.status_code >= 400:
					messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
			for chapter in chapters:
				response = do_patch(f'api/chapters/{chapter["id"]}/', request, data=chapter, object_name='Work')
				if response.response_info.status_code >= 400:
					messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
			if work_dict[4]:
				data = {'id': id, 'draft': False}
				response = do_patch(f'api/works/{id}/publish-full/', request, data=data, object_name='Work And Chapters')
		else:
			messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
		if work_dict[1] == 'false':
			return redirect(f'/works/{id}')
		else:
			return redirect(f'/works/{id}/chapters/new?count={len(chapters)}')
	else:
		if request.user.is_authenticated:
			multichapter = request.GET.get('multichapter', 'false')
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
			chapter_count = int(work['chapter_count'])
			if chapter_count < 2:
				work_chapter = do_get(f'api/works/{id}/chapters', request, 'Chapter').response_data['results'][0] if chapter_count > 0 else {'title': '','number': 1}
			else:
				work_chapter = chapters[0]
			work_chapter = prepare_chapter_data(work_chapter, request)
			tags = group_tags_for_edit(work['tags'], tag_types) if 'tags' in work else group_tags_for_edit([], tag_types)
			return render(request, 'work_form.html', {
				'work_types': work_types['results'],
				'form_title': 'Edit Work',
				'work': work,
				'tags': tags,
				'multichapter': multichapter,
				'divider': settings.TAG_DIVIDER,
				'show_chapter': request.GET.get('show_chapter') if 'show_chapter' in request.GET else None,
				'chapters': chapters,
				'work_chapter': work_chapter,
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
	message_type = messages.ERROR if file_url.response_info.status_code >= 400 else messages.SUCCESS
	if not message_type == messages.SUCCESS:
		messages.add_message(request, message_type, file_url.response_info.message, file_url.response_info.type_label)
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
	referrer = request.META.get('HTTP_REFERER')
	if f'works/{work_id}' in referrer:
		return redirect('/')
	return referrer_redirect(request, referrer)


def delete_chapter(request, work_id, chapter_id):
	response = do_delete(f'api/chapters/{chapter_id}/', request, object_name='Chapter')
	process_message(request, response)
	return redirect(f'/works/{work_id}/edit/?show_chapter=true')


def new_bookmark(request, work_id):
	if request.user.is_authenticated and request.method != 'POST':
		bookmark_boilerplate = get_bookmark_boilerplate(request, work_id)
		return render(request, 'bookmark_form.html', {
			'tags': bookmark_boilerplate[1],
			'divider': settings.TAG_DIVIDER,
			'rating_range': bookmark_boilerplate[2],
			'form_title': 'New Bookmark',
			'bookmark':  bookmark_boilerplate[0]})
	elif request.user.is_authenticated:
		bookmark_dict = get_bookmark_obj(request)
		if 'rating' not in bookmark_dict:
			bookmark_dict['rating'] = 0
		elif len(bookmark_dict['rating']) > 1:
			bookmark_dict['rating'] = 0
		response = do_post(f'api/bookmarks/', request, data=bookmark_dict, object_name='Bookmark')
		process_message(request, response)
		if 'id' not in response.response_data:
			bookmark_boilerplate = get_bookmark_boilerplate(request, work_id)
			return render(request, 'bookmark_form.html', {
				'tags': bookmark_boilerplate[1],
				'divider': settings.TAG_DIVIDER,
				'rating_range': bookmark_boilerplate[2],
				'form_title': 'New Bookmark',
				'bookmark':  bookmark_boilerplate[0]})
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
			tags = group_tags_for_edit(bookmark['tags'], tag_types) if 'tags' in bookmark else group_tags_for_edit([], tag_types)
			return render(request, 'bookmark_form.html', {
				'rating_range': bookmark['star_count'],
				'divider': settings.TAG_DIVIDER,
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
	bookmark_collections = format_date_for_template(bookmark_collections, 'updated_on', True)
	for bkcol in bookmark_collections:
		bkcol['attributes'] = get_attributes_for_display(bkcol['attributes'])
	return render(request, 'bookmark_collections.html', {
		'bookmark_collections': bookmark_collections,
		'next': f"/bookmarkcollections/{response['next_params']}" if response['next_params'] is not None else None,
		'previous': f"/bookmarkcollections/{response['prev_params']}" if response['prev_params'] is not None else None,
		'root': settings.ROOT_URL})


def new_bookmark_collection(request):
	if request.user.is_authenticated and request.method != 'POST':
		bookmark_collection = {
			'title': 'New Bookmark Collection',
			'description': '',
			'user': request.user.username,
			'is_private': True,
			'is_draft': True,
			'anon_comments_permitted': True,
			'comments_permitted': True
		}
		bookmark_collection_attributes = do_get(f'api/attributetypes', request, params={'allow_on_bookmark_collection': True}, object_name='Attribute')
		bookmark_collection['attribute_types'] = process_attributes([], bookmark_collection_attributes.response_data['results'])
		tag_types = do_get(f'api/tagtypes', request, 'Tag Type').response_data
		tags = group_tags_for_edit([], tag_types)
		bookmarks = do_get(f'api/users/{request.user.username}/bookmarks?draft=false', request, 'Bookmarks').response_data
		return render(request, 'bookmark_collection_form.html', {
			'tags': tags,
			'divider': settings.TAG_DIVIDER,
			'form_title': _('New Collection'),
			'bookmark_collection': bookmark_collection,
			'bookmarks': bookmarks})
	elif request.user.is_authenticated:
		collection_dict = get_bookmark_collection_obj(request)
		response = do_post(f'api/bookmarkcollections/', request, data=collection_dict, object_name='Bookmark Collection')
		process_message(request, response)
		if 'id' in response.response_data:
			return redirect(f'/bookmark-collections/{response.response_data["id"]}')
		else:
			return redirect(f'/bookmark-collections/new')
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
			bookmarks = do_get(f'api/users/{request.user.username}/bookmarks?draft=false', request, 'Bookmarks')
			return render(request, 'bookmark_collection_form.html', {
				'bookmark_collection': bookmark_collection,
				'bookmarks': bookmarks,
				'divider': settings.TAG_DIVIDER,
				'form_title': 'Edit Bookmark Collection',
				'tags': tags})
		else:
			return get_unauthorized_message(request, '/login', 'bookmark-collection-update-login-error')


def get_bookmarks_for_collection(request):
	bookmarks = do_get(f'api/users/{request.user.username}/bookmarks', request, params=request.GET, object_name='Bookmarks')
	return render(request, 'collection_form_bookmark_modal_body.html', {
		'bookmarks': bookmarks
	})


def bookmark_collection(request, pk):
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	scroll_comment_id = request.GET['scrollCommentId'] if'scrollCommentId' in request.GET else None
	comment_id = request.GET.get('comment_thread')
	comment_offset = request.GET.get('comment_offset') if request.GET.get('comment_offset') else 0
	comment_count = request.GET.get('comment_count')
	cache_key = f'collection_{pk}_{request.user}_{expand_comments}_{scroll_comment_id}_{comment_id}_{comment_offset}_{comment_count}'
	if cache.get(cache_key):
		return cache.get(cache_key)
	bookmark_collection = do_get(f'api/bookmarkcollections/{pk}', request, 'Bookmark Collection').response_data
	tags = group_tags(bookmark_collection['tags']) if 'tags' in bookmark_collection else {}
	bookmark_collection['tags'] = tags
	bookmark_collection['attributes'] = get_attributes_for_display(bookmark_collection['attributes'])
	bookmark_collection = format_date_for_template(bookmark_collection, 'updated_on')
	if 'comment_thread' in request.GET:
		comments = do_get(f"api/collectioncomments/{comment_id}", request, 'Bookmark Collection Comments').response_data
		comment_offset = 0
		comments = {'results': [comments], 'count': comment_count}
		bookmark_collection['post_action_url'] = f"/bookmark-collections/{pk}/comments/new?offset={comment_offset}&comment_thread={comment_id}"
		bookmark_collection['edit_action_url'] = f"""/bookmark-collections/{pk}/comments/edit?offset={comment_offset}&comment_thread={comment_id}"""
	else:
		comments = do_get(f'api/bookmarkcollections/{pk}/comments?limit=10&offset={comment_offset}', request, 'Bookmark Collection Comments').response_data
		bookmark_collection['post_action_url'] = f"/bookmark-collections/{pk}/comments/new"
		bookmark_collection['edit_action_url'] = f"""/bookmark-collections/{pk}/comments/edit"""
	for bookmark in bookmark_collection['bookmarks_readonly']:
		bookmark['description'] = bookmark['description'].replace('<p>', '<br/>').replace('</p>', '').replace('<br/>', '', 1)
	user_can_comment = (bookmark_collection['comments_permitted'] and (bookmark_collection['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in bookmark_collection else False
	bookmark_collection['new_action_url'] = f"/bookmark-collections/{pk}/comments/new"
	comments['results'] = format_comments_for_template(comments['results'])
	page_content = render(request, 'bookmark_collection.html', {
		'load_more_base': f"/bookmark-collections/{pk}",
		'view_thread_base': f"/bookmark-collections/{pk}",
		'bkcol': bookmark_collection,
		'comment_offset': comment_offset,
		'scroll_comment_id': scroll_comment_id,
		'expand_comments': expand_comments,
		'user_can_comment': user_can_comment,
		'comments': comments})
	if not cache.get(cache_key) and len(messages.get_messages(request)) < 1:
		cache.set(cache_key, page_content, 60 * 60)
	return page_content


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
			referrer = request.POST.get('referrer')
			if not referrer:
				referrer = '/'
			return render(request, 'login.html', {'referrer': referrer})
	else:
		if request.user.is_authenticated:
			return referrer_redirect(request)
		if 'HTTP_REFERER' in request.META:
			referrer = request.META['HTTP_REFERER']
			if 'register' in referrer:
				referrer = '/'
			return render(request, 'login.html', {'referrer': referrer})
		else:
			return render(request, 'login.html', {'referrer': '/'})


def reset_password(request):
	if request.method == 'POST':
		user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
		if user is not None:
			login(request, user)
			messages.add_message(request, messages.SUCCESS, _('Reset successful.'), 'reset-login-success')
			return redirect('/')
		else:
			messages.add_message(request, messages.ERROR, _('Reset unsuccessful. Please try again.'), 'reset-login-error')
			return redirect('/login')
	else:
		if request.user.is_authenticated:
			return referrer_redirect(request)
		if 'HTTP_REFERER' in request.META:
			return render(request, 'login.html', {
				'referrer': request.META['HTTP_REFERER']})
		else:
			return render(request, 'login.html', {
				'referrer': '/'})


def register(request):
	if request.user.is_authenticated:
		messages.add_message(request, messages.ERROR, _('You are already logged in.'), 'register-while-authed-error')
		return redirect('/')
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
			return redirect(f'/register?username={request.POST.get("username")}&email={request.POST.get("email")}')
	else:
		if 'invite_token' in request.GET:
			response = do_get(f'api/invitations/', request, params={'email': request.GET.get('email'), 'invite_token': request.GET.get('invite_token')}, object_name='Invite Code')
			if response.response_info.status_code == 200:
				return render(request, 'register.html', {'permit_registration': True, 'invite_code': response.response_data['invitation']})
			if response.response_info.status_code == 418:
				messages.add_message(request, messages.ERROR, response.response_info.message, response.response_info.type_label)
				return redirect('/')
			else:
				messages.add_message(request, messages.ERROR, _('Your invite code or email is incorrect. Please check your link again and contact site admin.'), 'register-invalid-token-error')
				return redirect('/')
		permit_registration = do_get(f'api/settings/', request, params={'setting_name': 'Registration Permitted'}, object_name='Setting').response_data
		invite_only = do_get(f'api/settings/', request, params={'setting_name': 'Invite Only'}, object_name='Setting').response_data
		mandatory_agree_pages = do_get(f'api/contentpages/mandatory-on-signup/', request, object_name='Page').response_data
		if not utils.convert_boolean(permit_registration['results'][0]['value']):
			return render(request, 'register.html', {'permit_registration': False})
		elif utils.convert_boolean(invite_only['results'][0]['value']):
			return redirect('/request-invite')
		else:
			return render(request, 'register.html', {
				'permit_registration': True,
				'mandatory_agree_pages': mandatory_agree_pages,
				'username_check_url': 'registration-utils',
				'email': request.GET.get('email', None),
				'username': request.GET.get('username', None)
			})


def request_invite(request):
	if request.method == 'POST':
		if not request.user.is_authenticated:
			if settings.USE_CAPTCHA:
				captcha_passed = validate_captcha(request)
				if not captcha_passed:
					messages.add_message(request, messages.ERROR, 'Captcha failed. Please try again.', 'captcha-fail-error')
					return redirect('/request-invite/')
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
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	comment_offset = request.GET.get('comment_offset') if request.GET.get('comment_offset') else 0
	comment_id = request.GET.get('comment_thread')
	comment_count = request.GET.get('comment_count')
	cache_key = f'work_{pk}_{chapter_offset}_{request.user}_{view_full}_{expand_comments}_{comment_offset}_{comment_id}_{comment_count}'
	if cache.get(cache_key):
		return cache.get(cache_key)
	work_types = do_get(f'api/worktypes', request, 'Work Type').response_data
	url = f'api/works/{pk}/'
	work_response = do_get(url, request, 'Work')
	if work_response.response_info.status_code >= 400:
		messages.add_message(request, messages.ERROR, work_response.response_info.message, work_response.response_info.type_label)
		return redirect('/')
	work = work_response.response_data
	tags = group_tags(work['tags']) if 'tags' in work else {}
	work['attributes'] = get_attributes_for_display(work['attributes'])
	work = format_date_for_template(work, 'updated_on')
	chapter_url_string = f'api/works/{pk}/chapters{"?limit=1" if view_full is False else "/all"}'
	if chapter_offset > 0:
		chapter_url_string = f'{chapter_url_string}&offset={chapter_offset}'
	chapter_response = do_get(chapter_url_string, request, 'Chapter').response_data
	chapter_json = chapter_response['results'] if 'results' in chapter_response else chapter_response
	user_can_comment = (work['comments_permitted'] and (work['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in work else False
	chapters = []
	for chapter in chapter_json:
		chapter = format_date_for_template(chapter, 'updated_on')
		if 'id' in chapter:
			if 'comment_thread' not in request.GET:
				chapter_comments = do_get(f"api/chapters/{chapter['id']}/comments?limit=10&offset={comment_offset}", request, "Chapter Comments").response_data
				chapter['post_action_url'] = f"/works/{pk}/chapters/{chapter['id']}/comments/new?offset={chapter_offset}"
				chapter['edit_action_url'] = f"""/works/{pk}/chapters/{chapter['id']}/comments/edit?offset={chapter_offset}"""
			else:
				chapter_comments = do_get(f"api/chaptercomments/{comment_id}", request, 'Chapter Comments').response_data
				comment_offset = 0
				chapter_comments = {'results': [chapter_comments], 'count': comment_count}
				chapter['post_action_url'] = f"/works/{pk}/chapters/{chapter['id']}/comments/new?offset={chapter_offset}&comment_thread={comment_id}"
				chapter['edit_action_url'] = f"""/works/{pk}/chapters/{chapter['id']}/comments/edit?offset={chapter_offset}&comment_thread={comment_id}"""
			chapter_comments['results'] = format_comments_for_template(chapter_comments['results'])
			chapter['comments'] = chapter_comments
			chapter['comment_offset'] = comment_offset
			chapter['load_more_base'] = f"/works/{pk}/chapters/{chapter['id']}/{chapter_offset}"
			chapter['view_thread_base'] = f"/works/{pk}/{chapter_offset}"
			chapter['attributes'] = get_attributes_for_display(chapter['attributes'])
			chapter['new_action_url'] = f"/works/{pk}/chapters/{chapter['id']}/comments/new?offset={chapter_offset}"
			chapters.append(chapter)
	page_content = render(request, 'work.html', {
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
	if not cache.get(cache_key) and len(messages.get_messages(request)) < 1:
		cache.set(cache_key, page_content, 60 * 60)
	return page_content


def render_comments_common(request, get_comment_base, object_name, object_id, load_more_base, view_thread_base, delete_obj, post_action_url, edit_action_url, root_obj_id=None, additional_params={}):
	limit = request.GET.get('limit', '')
	offset = request.GET.get('offset', '')
	depth = request.GET.get('depth', 0)
	comments = do_get(f'{get_comment_base}/comments?limit={limit}&offset={offset}', request, 'Comments').response_data
	comments['results'] = format_comments_for_template(comments['results'])
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
	if comment_count > 9 and request.POST.get('parent_comment') is None:
		comment_offset = int(int(request.POST.get(f'{object_name}_comment_count')) / 10) * 10
	elif comment_count > 9 and request.POST.get('parent_comment') is not None:
		comment_offset = request.POST.get('parent_comment_next')
	else:
		comment_offset = 0
	if request.user.is_authenticated:
		comment_dict["user"] = str(request.user)
	else:
		comment_dict["user"] = None
	if request.GET.get("offset", None):
		comment_dict['offset'] = request.GET.get("offset")
	if comment_thread:
		comment_dict['comment_thread'] = comment_thread
		comment_dict['comment_count'] = comment_count
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
	return delete_comment_common(request, request.headers.get('Referer'), 'chapter', comment_id)


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
	bookmarks = format_date_for_template(bookmarks, 'updated_on', True)
	for bookmark in bookmarks:
		bookmark['attributes'] = get_attributes_for_display(bookmark['attributes'])
	return render(request, 'bookmarks.html', {
		'bookmarks': bookmarks,
		'rating_range': response['star_count'],
		'next': f"/bookmarks/{next_param}" if next_param is not None else None,
		'previous': f"/bookmarks/{previous_param}" if previous_param is not None else None})


def bookmark(request, pk):
	comment_id = request.GET.get('comment_thread')
	comment_count = request.GET.get('comment_count')
	comment_offset = request.GET.get('comment_offset') if request.GET.get('comment_offset') else 0
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	scroll_comment_id = request.GET['scrollCommentId'] if'scrollCommentId' in request.GET else None
	cache_key = f'bookmark_{pk}_{request.user}_{comment_id}_{comment_count}_{comment_offset}_{expand_comments}_{scroll_comment_id}'
	if cache.get(cache_key):
		return cache.get(cache_key)
	bookmark = do_get(f'api/bookmarks/{pk}', request, 'Bookmark').response_data
	if 'id' not in bookmark or not bookmark['id']:
		messages.add_message(request, messages.ERROR, _('Bookmark not found.'), 'bookmark-not-found')
		return referrer_redirect(request)
	tags = group_tags(bookmark['tags']) if 'tags' in bookmark else {}
	bookmark['attributes'] = get_attributes_for_display(bookmark['attributes']) if 'attributes' in bookmark else {}
	bookmark = format_date_for_template(bookmark, 'updated_on')
	if 'comment_thread' in request.GET:
		comments = do_get(f"api/bookmarkcomments/{comment_id}", request, 'Bookmark Comments').response_data
		comment_offset = 0
		comments = {'results': [comments], 'count': comment_count}
		bookmark['post_action_url'] = f"/bookmarks/{pk}/comments/new?offset={comment_offset}&comment_thread={comment_id}"
		bookmark['edit_action_url'] = f"""/bookmarks/{pk}/comments/edit?offset={comment_offset}&comment_thread={comment_id}"""
	else:
		comments = do_get(f'api/bookmarks/{pk}/comments?limit=10&offset={comment_offset}', request, 'Bookmark Comment').response_data
		bookmark['post_action_url'] = f"/bookmarks/{pk}/comments/new"
		bookmark['edit_action_url'] = f"""/bookmarks/{pk}/comments/edit"""
	comments['results'] = format_comments_for_template(comments['results'])
	bookmark['new_action_url'] = f"/bookmarks/{pk}/comments/new"
	user_can_comment = (bookmark['comments_permitted'] and (bookmark['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in bookmark else False
	collections = do_get(f'api/users/{request.user.username}/bookmarkcollections', request, 'Collections').response_data
	page_content = render(request, 'bookmark.html', {
		'bookmark': bookmark,
		'collections': collections,
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
	if not cache.get(cache_key) and len(messages.get_messages(request)) < 1:
		cache.set(cache_key, page_content, 60 * 60)
	return page_content


def add_collection_to_bookmark(request, pk):
	collection_id = request.GET.get('collection_id')
	if not collection_id:
		return redirect(f'/bookmarks/{pk}')
	if not request.user.is_authenticated:
		messages.add_message(request, messages.ERROR, _('You must log in to perform this action.'), 'add-collection-to-bookmark-noauth')
	response = do_patch(f'api/bookmarks/{pk}/', request, data={'id': pk, 'collection': collection_id}, object_name="Collection")
	message_type = messages.ERROR if response.response_info.status_code >= 400 else messages.SUCCESS
	messages.add_message(request, message_type, response.response_info.message, response.response_info.type_label)
	return redirect(f'/bookmarks/{pk}')


def works_by_tag(request, tag):
	return search(request)


def works_by_attribute(request, attribute):
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
