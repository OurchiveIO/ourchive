from django.shortcuts import render, redirect
import requests
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, logout, login
from django.contrib import messages
from django.contrib.auth.models import User
import json
from .file_helpers import FileHelperService
import threading
from django.http import HttpResponse
from .search_models import SearchObject
from html import escape
import logging

logger = logging.getLogger(__name__)

def group_tags(tag_types, tags):
	result = {}
	for tag_type in tag_types:
		result[tag_type['label']] = []
	for tag in tags:
		result[tag['tag_type']].append(tag)
	return result

def get_headers(request):
	headers = {}
	headers['X-CSRFToken'] = request.COOKIES['csrftoken'] if 'csrftoken' in request.COOKIES else None
	headers['content-type'] = 'application/json'
	return headers

def append_root_url(url):
	return f"{settings.API_PROTOCOL}{settings.ALLOWED_HOSTS[0]}/{url}"

def get_results(results):
	try:
		results_json = results.json() if (results.status_code != 204 and results.status_code != 500 and results.status_code != 403 and results.status_code != 404) else {}
	except Exception as e:
		logger.error(f"exception: {e}")
		logger.debug(f"exception occurred: {e}")
		results_json = {}
	results_status_code = results.status_code
	logger.debug(f"status code: {results_status_code}")
	return [results_json, results_status_code]

def sanitize_rich_text(rich_text):
	if rich_text is not None:
		rich_text = escape(rich_text) 
	else:
		rich_text =''
	return rich_text

def process_results(results, object):
	if results[1] >= 200 and results[1] < 300:
		return 'OK'
	if results[1] >= 400 and results[1] < 500 and results[1] != 404:
		return f"You are not authorized to access this {object}. Please contact your administrator for more information."
	if results[1] == 404:
		return f"We could not find this {object}. You may not have access to it, or it may not exist."
	if results[1] == 500:
		f"An error occurred while accessing this {object}. Please contact your administrator for more information."
 
def do_patch(url, request, data={}):
	return get_results(requests.patch(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request)))

def do_post(url, request, data={}):
	return get_results(requests.post(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request)))

def do_put(url, request, data={}):
	return get_results(requests.put(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request)))

def do_delete(url, request):
	return get_results(requests.delete(append_root_url(url), cookies=request.COOKIES, headers=get_headers(request)))

def do_get(url, request, params={}):
	return get_results(requests.get(append_root_url(url), params=params, cookies=request.COOKIES, headers=get_headers(request)))

def get_object_tags(parent, request):
	tag_types = do_get('api/tagtypes', request)
	result_message = process_results(tag_types, 'tag types')
	if result_message != 'OK':
		messages.add_message(request, messages.ERROR, result_message)
	else:
		tag_types = tag_types[0]
		for item in parent:
			tags = group_tags(tag_types['results'], item['tags']) if 'tags' in item else {}
			item['tags'] = tags
	return parent

def get_works_list(request, username=None):
	url = f'api/users/{username}/works' if username is not None else f'api/works'
	response = do_get(url, request, params=request.GET)
	result_message = process_results(response, 'works')
	if result_message !='OK':
		messages.add_message(request, messages.ERROR, result_message)
		return redirect('/')
	else:
		works = response[0]['results']
		works = get_object_tags(works, request)
	return {'works': works, 'next_params': response['next_params'], 'prev_params': response['prev_params']}

def index(request):
	if request.user.is_authenticated:
		request_url = f"api/users/{request.user.id}/"
		response = do_get(request_url, request)[0]
		if 'userprofile' in response and response['userprofile'] is not None and 'has_notifications' in response['userprofile']:
			has_notifications = response['userprofile']['has_notifications']
			request.session['has_notifications'] = has_notifications
		else:
			request.session['has_notifications'] = False
	else:
		request.session['has_notifications'] = False
	return render(request, 'index.html', {
	    'heading_message': 'Welcome to Ourchive',
	    'long_message': 'Ourchive is a configurable, extensible, multimedia archive, meant to serve as a modern alternative to PHP-based archives. You can search for existing works, create your own, or create curated collections of works you\'ve enjoyed. Have fun with it!',
		'root': settings.ALLOWED_HOSTS[0],
		'has_notifications': request.session['has_notifications']
	})

def user_name(request, username):
	user = do_get(f"api/users/{username}", request)[0]
	if len(user['results']) > 0:
		work_params = {}
		bookmark_params = {}
		anchor = None
		if 'work_offset' in request.GET:
			work_params['offset'] = request.GET['work_offset']
			work_params['limit'] = request.GET['work_limit']
			anchor = "work_tab"
		if 'bookmark_offset' in request.GET:
			bookmark_params['offset'] = request.GET['bookmark_offset']
			bookmark_params['limit'] = request.GET['bookmark_limit']
			anchor = "bookmark_tab"
		works_response = do_get(f'api/users/{username}/works', request, params=work_params)[0]
		works = works_response['results']
		works = get_object_tags(works, request)
		work_next = f'/username/{username}/{works_response["next_params"].replace("limit=", "work_limit=").replace("offset=", "work_offset=")}' if works_response["next_params"] is not None else None
		work_previous = f'/username/{username}/{works_response["prev_params"].replace("limit=", "work_limit=").replace("offset=", "work_offset=")}' if works_response["prev_params"] is not None else None
		bookmarks_response = do_get(f'api/users/{username}/bookmarks', request, params=bookmark_params)[0]
		bookmarks = bookmarks_response['results']
		bookmark_next = f'/username/{username}/{bookmarks_response["next_params"].replace("limit=", "bookmark_limit=").replace("offset=", "bookmark_offset=")}' if bookmarks_response["next_params"] is not None else None
		bookmark_previous = f'/username/{username}/{bookmarks_response["prev_params"].replace("limit=", "bookmark_limit=").replace("offset=", "bookmark_offset=")}' if bookmarks_response["prev_params"] is not None else None
		bookmarks = get_object_tags(bookmarks, request)
		return render(request, 'user.html', {
			'bookmarks': bookmarks, 
			'bookmarks_next': bookmark_next,
			'bookmarks_previous': bookmark_previous,
			'user_filter': username,
			'root': settings.ALLOWED_HOSTS[0],
			'works': works,
			'anchor': anchor,
			'works_next': work_next,
			'works_previous': work_previous,
			'user': user['results'][0]
		})
	else:
		messages.add_message(request, messages.ERROR, 'User not found.')
		return redirect('/')

def user_block_list(request, username):
	blocklist = do_get(f'api/users/{username}/userblocks', request)
	if blocklist[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to view this blocklist.')	
		return redirect(f'/username/{username}')
	return render(request, 'user_block_list.html', {
		'blocklist': blocklist[0]['results'],
		'username': username
	})

def block_user(request, username):
	data = {'user': request.user.username, 'blocked_user': username}
	blocklist = do_post(f'api/userblocks', request, data)
	if blocklist[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to view this blocklist.')	
	if blocklist[1] >= 200 and blocklist[1] < 300:
		messages.add_message(request, messages.SUCCESS, 'User blocked.')
	return redirect(f'/username/{username}')

def unblock_user(request, username, pk):
	blocklist = do_delete(f'api/userblocks/{pk}', request)
	if blocklist[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to unblock this user.')	
	if blocklist[1] >= 200 and blocklist[1] < 300:
		messages.add_message(request, messages.SUCCESS, 'User unblocked.')
	return redirect(f'/username/{username}')

def user_works(request, username):
	works = get_works_list(request, username)
	return render(request, 'works.html', {
		'works': works['works'],
		'next': f"/username/{username}/works/{works['next_params']}" if works["next_params"] is not None else None,
		'previous': f"/username/{username}/works/{works['prev_params']}" if works["prev_params"] is not None else None,
		'user_filter': username,
		'root': settings.ALLOWED_HOSTS[0]})

def user_works_drafts(request, username):
	response = do_get(f'api/users/{username}works/drafts', request)[0]
	works = response['results']
	works = get_object_tags(works, request)
	return render(request, 'works.html', {
		'works': works,
		'user_filter': username,
		'root': settings.ALLOWED_HOSTS[0]})

def edit_account(request, username):
	if request.method == 'POST':
		user_data = request.POST.copy()
		profile_id = user_data['id']
		user_data.pop('id')
		response = do_patch(f'api/users/{profile_id}/', request, data=user_data)
		if response[1] == 200:
			messages.add_message(request, messages.SUCCESS, 'Account information updated.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to update this account.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while updating this account. Please contact your administrator.')	
		return redirect('/username/'+username)
	else:
		if request.user.is_authenticated:			
			response = do_get(f'api/users/{username}', request)[0]
			user = response['results']
			if len(user) > 0:
				user = user[0]
				return render(request, 'account_form.html', {'user': user})
			else:
				messages.add_message(request, messages.ERROR, 'User information not found. Please contact your administrator.')	
				return redirect('/username/'+username)
		else:
			messages.add_message(request, messages.ERROR, 'You must log in as this user to perform this action.')	
			return redirect('/login')

def edit_user(request, username):
	if request.method == 'POST':
		if 'files[]' in request.FILES:
			service = FileHelperService.get_service()
			if service is not None:
				final_url = service.handle_uploaded_file(request.FILES['files[]'], request.FILES['files[]'].name, request.user.username)
				return HttpResponse(final_url)
			else:
				messages.add_message(request, messages.ERROR, 'This instance is trying to use a file processor not supported by file helpers. Please contact your administrator.')	
				return HttpResponse('')
		user_data = request.POST.copy()
		if user_data['icon'] == "":
			user_data['icon'] = user_data['unaltered_icon']
		user_data.pop('unaltered_icon')
		profile_id = user_data['userprofile_id']
		user_data.pop('userprofile_id')
		if profile_id:
			response = do_put(f'api/userprofile/{profile_id}/', request, data=user_data)
		else:
			response = do_post(f'api/userprofiles', request, data=user_data)
		if response[1] == 200 or response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'User profile updated.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to update this user profile.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while updating this user profile. Please contact your administrator.')	
		return redirect('/username/'+username)
	else:
		if request.user.is_authenticated:			
			response = do_get(f'api/users/{username}', request)
			user = response[0]['results']
			if len(user) > 0:
				user = user[0]
				if user['userprofile'] is not None:
					user['userprofile']['profile'] = sanitize_rich_text(user['userprofile']['profile']) 
				return render(request, 'user_form.html', {'user': user})
			else:
				messages.add_message(request, messages.ERROR, 'User information not found. Please contact your administrator.')	
				return redirect('/username/'+username)
		else:
			messages.add_message(request, messages.ERROR, 'You must log in as this user to perform this action.')	
			return redirect('/login')

def user_bookmarks(request, username):
	response = do_get(f'api/users/{username}/bookmarks', request, params=request.GET)[0]
	bookmarks = response['results']
	bookmarks = get_object_tags(bookmarks, request)
	return render(request, 'bookmarks.html', {
		'bookmarks': bookmarks, 
		'next': f"/username/{username}/bookmarks/{response['next_params']}" if response["next_params"] is not None else None,
		'previous': f"/username/{username}/bookmarks/{response['prev_params']}" if response["prev_params"] is not None else None,
		'user_filter': username})

def user_notifications(request, username):
	if request.user.is_authenticated:
		response = do_get(f'api/users/{request.user.id}/', request, params=request.GET)
		if response[0] is not None and response[0]['userprofile'] is not None:
			has_notifications = response[0]['userprofile']['has_notifications']
			request.session['has_notifications'] = has_notifications
	else:
		request.session['has_notifications'] = False
	response = do_get(f'api/users/{username}/notifications', request, params=request.GET)
	if response[1] == 204 or response[1] == 200:
		notifications = response[0]['results']
		return render(request, 'notifications.html', {
			'notifications': notifications,
			'next': f"/username/{username}/notifications/{response[0]['next_params']}" if response[0]['next_params'] is not None else None,
			'previous': f"/username/{username}/notifications/{response[0]['prev_params']}" if response[0]['prev_params'] is not None else None})	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to view these notifications.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while fetching notifications. Please contact your administrator.')	
	return redirect(f'/')
	
def delete_notification(request, username, notification_id): 
	response = do_delete(f'api/notifications/{notification_id}', request)
	if response[1] == 204:
		messages.add_message(request, messages.SUCCESS, 'Notification deleted.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to delete this notification.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while deleting this notification. Please contact your administrator.')	
	return redirect(f'/username/{username}/notifications')

def mark_notification_read(request, username, notification_id): 
	data = {'id': notification_id, 'read': True}
	response = do_patch(f'api/notifications/{notification_id}/', request, data=data)
	if response[1] == 200:
		messages.add_message(request, messages.SUCCESS, 'Notification marked as read.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to modify this notification.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while modifying this notification. Please contact your administrator.')	
	return redirect(f'/username/{username}/notifications')

def user_bookmarks_drafts(request, username):
	response = do_get(f'api/users/{username}/bookmarks/drafts', request)
	bookmarks = response[0]['results']
	bookmarks = get_object_tags(bookmarks, request)
	return render(request, 'bookmarks.html', {'bookmarks': bookmarks, 'user_filter': username})

def search(request):
	tag_types_json = do_get(f'api/tagtypes', request)[0]
	if 'term' in request.GET:
		term = request.GET['term']
	else:
		term = request.POST['term']
	request_builder = SearchObject()
	request_object = request_builder.with_term(term)
	response_json = do_post(f'api/search/', request, data=request_object)[0]
	works = response_json['results']['work']
	works = get_object_tags(works, request)
	bookmarks = response_json['results']['bookmark']
	bookmarks = get_object_tags(bookmarks, request)
	tags = group_tags(tag_types_json['results'], response_json['results']['tag'])
	tag_count = len(response_json['results']['tag'])
	users = response_json['results']['user']
	return render(request, 'search_results.html', {'works': works, 'bookmarks': bookmarks,
		'tags': tags, 'users': users, 'tag_count': tag_count, 'facets': response_json['results']['facet'],
		'root': settings.ALLOWED_HOSTS[0], 'term': term})

def search_filter(request):
	tag_types_json = do_get(f'api/tagtypes', request)[0]
	term = request.POST['term']
	request_builder = SearchObject()
	request_object = request_builder.with_term(term)
	for key in request.POST:
		filter_val = request.POST[key]
		if filter_val == 'csrfmiddlewaretoken':
			continue
		if filter_val == 'term':
			continue
		else:
			filter_options = key.split('|')
			for option in filter_options:
				filter_details = option.split('$')
				filter_type = request_builder.get_object_type(filter_details[0])
				if filter_type == 'work':
					if len(request_object['work_search']['filter'][filter_details[0]]) > 0:
						request_object['work_search']['filter'][filter_details[0]].append(filter_details[1])
					else:
						request_object['work_search']['filter'][filter_details[0]] = []
						request_object['work_search']['filter'][filter_details[0]].append(filter_details[1])
				elif filter_type == 'tag':
					tag_type = filter_details[0].split(',')[1]
					tag_text = filter_details[1].split(',')[1]
					request_object['tag_search']['filter']['tag_type'].append(tag_type)
					request_object['tag_search']['filter']['text'].append(tag_text)
				elif filter_type == 'bookmark':
					if len(request_object['bookmark_search']['filter'][filter_details[0]]) > 0:
						request_object['bookmark_search']['filter'][filter_details[0]].append(filter_details[1])
					else:
						request_object['bookmark_search']['filter'][filter_details[0]] = []
						request_object['bookmark_search']['filter'][filter_details[0]].append(filter_details[1])
	response_json = do_post(f'api/search/', request, data=request_object)[0]
	works = response_json['results']['work']
	works = get_object_tags(works, request)
	bookmarks = response_json['results']['bookmark']
	bookmarks = get_object_tags(bookmarks, request)
	tags = group_tags(tag_types_json['results'], response_json['results']['tag'])
	tag_count = len(response_json['results']['tag'])
	users = response_json['results']['user']
	return render(request, 'search_results.html', {'works': works, 'bookmarks': bookmarks,
		'tags': tags, 'users': users, 'tag_count': tag_count, 'facets': response_json['results']['facet'],
		'root': settings.ALLOWED_HOSTS[0], 'term': term})
				
@require_http_methods(["GET"])
def works(request):
	works_response = do_get(f'api/works/', request, params=request.GET)[0]
	works = works_response['results']
	works = get_object_tags(works, request)
	return render(request, 'works.html', {
		'works': works,
		'next': f"/works/{works_response['next_params']}" if works_response['next_params'] is not None else None,
		'previous': f"/works/{works_response['prev_params']}" if works_response['prev_params'] is not None else None,
		'root': settings.ALLOWED_HOSTS[0]})

def works_by_type(request, type_id):
	response = do_get(f'api/worktypes/{type_id}/works', request)[0]
	works = response['results']
	works = get_object_tags(works, request)
	return render(request, 'works.html', {
		'works': works,
		'root': settings.ALLOWED_HOSTS[0]})

def new_work(request):
	work_types = do_get(f'api/worktypes', request)[0]
	if request.user.is_authenticated and request.method != 'POST':
		response = do_post(f'api/works/', request, data={'title': 'Untitled Work', 'user': request.user.username})
		if response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Work created.')	
			work = response[0]
			tag_types = do_get(f'api/tagtypes', request)[0]
			tags = group_tags(tag_types['results'], [])
			return render(request, 'work_form.html', {'tags': tags, 'work_types': work_types['results'],
			'work': work})
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to create this work.')	
			return redirect('/works')
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while creating this work. Please contact your administrator.')	
			return redirect('/works')		
	elif request.user.is_authenticated:
		return edit_work(request, int(request.POST['work_id']))
	else:
		messages.add_message(request, messages.ERROR, 'You must log in to post a new work.')	
		return redirect('/login')

def new_chapter(request, work_id):
	if request.user.is_authenticated and request.method != 'POST':
		count = request.GET.get('count') if request.GET.get('count') != '' else 0
		request_json = {'title': 'Untitled Chapter', 'work': work_id, 'text': '', 'number': int(count) + 1}
		response = do_post(f'api/chapters/', request, data=request_json)
		if response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Chapter created.')	
			chapter = response[0]
			return render(request, 'chapter_form.html', {'chapter': chapter})
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to create this chapter.')	
			return redirect('/works/'+str(work_id))
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while creating this chapter. Please contact your administrator.')	
			return redirect('/works/'+str(work_id))
	elif request.user.is_authenticated:
		if 'chapter_id' in request.POST:
			return edit_chapter(request, work_id, request.POST['chapter_id'])
		else:
			return edit_chapter(request, work_id, None)
	else:
		messages.add_message(request, messages.ERROR, 'You must log in to post a new work.')	
		return redirect('/login')

def edit_chapter(request, work_id, id):
	if request.method == 'POST':
		if 'files[]' in request.FILES:
			service = FileHelperService.get_service()
			if service is not None:
				final_url = service.handle_uploaded_file(request.FILES['files[]'], request.FILES['files[]'].name, request.user.username)
				return HttpResponse(final_url)
			else:
				messages.add_message(request, messages.ERROR, 'This instance is trying to use a file processor not supported by file helpers. Please contact your administrator.')	
				return HttpResponse('')
		else:
			chapter_dict = request.POST.copy()
			chapter_dict["draft"] = "draft" in chapter_dict
			response = do_put(f'api/chapters/{id}/', request, data=chapter_dict)
			if response[1] == 200:
				messages.add_message(request, messages.SUCCESS, 'Chapter updated.')	
			elif response[1] == 403:
				messages.add_message(request, messages.ERROR, 'You are not authorized to update this chapter.')	
			else:
				messages.add_message(request, messages.ERROR, 'An error has occurred while updating this chapter. Please contact your administrator.')	
			return redirect('/works/'+str(work_id)+'/edit/?show_chapter=true')
	else:
		if request.user.is_authenticated:			
			chapter = do_get(f'api/chapters/{id}', request)[0]
			chapter['text'] = sanitize_rich_text(chapter['text'])
			chapter['summary'] = sanitize_rich_text(chapter['summary'])
			chapter['notes'] = sanitize_rich_text(chapter['notes'])
			return render(request, 'chapter_form.html', {'chapter': chapter})
		else:
			messages.add_message(request, messages.ERROR, 'You must log in to perform this action.')	
			return redirect('/login')

def edit_work(request, id):
	if request.method == 'POST':
		if 'files[]' in request.FILES:
			service = FileHelperService.get_service()
			if service is not None:
				final_url = service.handle_uploaded_file(request.FILES['files[]'], request.FILES['files[]'].name, request.user.username)
				return HttpResponse(final_url)
			else:
				messages.add_message(request, messages.ERROR, 'This instance is trying to use a file processor not supported by file helpers. Please contact your administrator.')	
				return HttpResponse('')
		work_dict = request.POST.copy()
		tags = []
		tag_types = {}
		chapters = []
		result = do_get(f'api/tagtypes', request)[0]['results']
		for item in result:
			tag_types[item['label']] = item
		for item in request.POST:
			if 'tags' in request.POST[item]:
				tag = {}				
				json_item = request.POST[item].split("_")
				tag['tag_type'] = json_item[2]
				tag['text'] = json_item[1]
				tags.append(tag)
				work_dict.pop(item)
			elif 'chapters_' in item:
				chapter_id = item[9:]
				chapter_number = request.POST[item]
				chapters.append({'id': chapter_id, 'number': chapter_number, 'work': id})
		work_dict["tags"] = tags
		comments_permitted = work_dict["comments_permitted"]
		work_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
		work_dict["anon_comments_permitted"] = comments_permitted == "All"
		redirect_toc = work_dict.pop('redirect_toc')[0]
		work_dict["is_complete"] = "is_complete" in work_dict
		work_dict["draft"] = "draft" in work_dict
		work_dict = work_dict.dict()
		work_dict["user"] = str(request.user)
		response = do_put(f'api/works/{id}/draft', request, data=work_dict)
		if response[1] == 200:
			for chapter in chapters:
				response = do_put(f'api/chapters/{chapter["id"]}/draft', request, data=chapter)
			messages.add_message(request, messages.SUCCESS, 'Work updated.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to update this work.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while updating this work. Please contact your administrator.')	
		if redirect_toc == 'false' and len(chapters) > 0:
			return redirect('/works/'+str(id))
		else:
			return redirect('/works/'+str(id)+'/chapters/new?count='+str(len(chapters)))
			
	else:
		work_types = do_get(f'api/worktypes', request)[0]
		tag_types = do_get(f'api/tagtypes', request)[0]
		if request.user.is_authenticated:
			work = do_get(f'api/works/{id}/draft', request)[0]
			work['summary'] = sanitize_rich_text(work['summary'])
			work['notes'] = sanitize_rich_text(work['notes'])
			chapters = do_get(f'api/works/{id}/chapters/draft', request)[0]
			tags = group_tags(tag_types['results'], work['tags'])
			return render(request, 'work_form.html', {'work_types': work_types['results'],
				'work': work, 
				'tags': tags,
				'show_chapter': request.GET.get('show_chapter') if 'show_chapter' in request.GET else None,
				'chapters': chapters['results'],
				'chapter_count': len(chapters)})
		else:
			messages.add_message(request, messages.ERROR, 'You must log in to perform this action.')	
			return redirect('/login')

def publish_work(request, id):
	data = {'id': id, 'draft': False}
	response = do_patch(f'api/works/{id}/', request, data=data)
	if response[1] == 200:
		messages.add_message(request, messages.SUCCESS, 'Work published.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to update this work.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while updating this work. Please contact your administrator.')	
	return redirect('/works/'+str(id))

def publish_chapter(request, work_id, chapter_id):
	data = {'id': chapter_id, 'draft': False}
	response = do_patch(f'api/chapters/{chapter_id}/', request, data=data)
	if response[1] == 200:
		messages.add_message(request, messages.SUCCESS, 'Chapter published.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to update this chapter.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while updating this chapter. Please contact your administrator.')	
	return redirect('/works/'+str(work_id))

def publish_work_and_chapters(request, id):
	data = {'id': id, 'draft': False}
	response = do_patch(f'api/works/{id}/publish-full/', request, data=data)
	if response[1] == 200:
		messages.add_message(request, messages.SUCCESS, 'Work and all chapters published.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to update this work.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while updating this work. Please contact your administrator.')	
	return redirect('/works/'+str(id))

def publish_bookmark(request, id):
	data = {'id': id, 'draft': False}
	response = do_patch(f'api/bookmarks/{id}/', request, data=data)
	if response[1] == 200:
		messages.add_message(request, messages.SUCCESS, 'Bookmark published.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to update this bookmark.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while updating this bookmark. Please contact your administrator.')	
	return redirect('/bookmarks/'+str(id))
			
def new_fingerguns(request, work_id):
	data = {'work': str(work_id), 'user': request.user.username}
	response = do_post(f'api/fingerguns/', request, data=data)
	if response[1] == 201:
		messages.add_message(request, messages.SUCCESS, 'Fingerguns added.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to add fingerguns to this work.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while adding fingerguns to this work. Please contact your administrator.')	
	return redirect('/works/'+str(work_id))

def delete_work(request, work_id):
	response = do_delete(f'api/works/{work_id}/', request)
	if response[1] == 204:
		messages.add_message(request, messages.SUCCESS, 'Work deleted.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to delete this work.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while deleting this work. Please contact your administrator.')	
	return redirect('/')

def delete_chapter(request, work_id, chapter_id):
	response = do_delete(f'api/chapters/{chapter_id}/', request)
	if response[1] == 204:
		messages.add_message(request, messages.SUCCESS, 'Chapter deleted.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to delete this chapter.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while deleting this chapter. Please contact your administrator.')	
	return redirect('/works/'+str(work_id)+'/edit/?show_chapter=true')

def new_bookmark(request, work_id):
	if request.user.is_authenticated and request.method != 'POST':
		data = {'title': '', 'user': request.user.username, 'work_id': work_id, 'is_private': True, 'rating': 5}
		response = do_post(f'api/bookmarks/', request, data=data)
		if response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Bookmark created.')	
			bookmark = response[0]
			tag_types = do_get(f'api/tagtypes', request)[0]
			tags = group_tags(tag_types['results'], bookmark['tags'])
			return render(request, 'bookmark_form.html', {'tags': tags, 'rating_range': [1,2,3,4,5],
			'bookmark': bookmark})
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to create this bookmark.')	
			return redirect('/')
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while creating this bookmark. Please contact your administrator.')	
			return redirect('/')		
	elif request.user.is_authenticated:
		return edit_bookmark(request, int(request.POST['bookmark_id']))
	else:
		messages.add_message(request, messages.ERROR, 'You must log in to create a bookmark.')	
		return redirect('/login')

def edit_bookmark(request, pk):
	if request.method == 'POST':
		bookmark_dict = request.POST.copy()
		tags = []
		tag_types = {}
		result = do_get(f'api/tagtypes', request)[0]['results']
		for item in result:
			tag_types[item['label']] = item
		for item in request.POST:
			dict_item = request.POST[item].replace('\'', '"')
			if 'tag_type_id' in request.POST[item]:				
				json_item = json.loads(dict_item)
				if not json_item['tag_type']:
					json_item['tag_type'] = tag_types[json_item['tag_type']]['url']
				tags.append(json_item)
				bookmark_dict.pop(item)
			elif 'tag_type' in request.POST[item]:				
				json_item = json.loads(dict_item)
				if not json_item['tag_type']:
					json_item['tag_type'] = tag_types[json_item['tag_type']]['url']
				tags.append(json_item)
				bookmark_dict.pop(item)
		bookmark_dict["tags"] = tags
		comments_permitted = bookmark_dict["comments_permitted"]
		bookmark_dict["comments_permitted"] = comments_permitted == "All" or comments_permitted == "Registered users only"
		bookmark_dict["anon_comments_permitted"] = comments_permitted == "All"
		bookmark_dict = bookmark_dict.dict()
		bookmark_dict["user"] = str(request.user)
		#bookmark_dict.pop("work")
		bookmark_dict["draft"] = 'draft' in bookmark_dict
		response = do_put(f'api/bookmarks/{pk}/', request, data=bookmark_dict)
		if response[1] == 200:			
			messages.add_message(request, messages.SUCCESS, 'Bookmark updated.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to update this bookmark.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while updating this bookmark. Please contact your administrator.')	
		return redirect('/bookmarks/'+str(pk))
			
	else:
		if request.user.is_authenticated:
			tag_types = do_get(f'api/tagtypes', request)[0]
			bookmark = do_get(f'api/bookmarks/{pk}/draft', request)[0]
			bookmark['description'] = sanitize_rich_text(bookmark['description'])
			tags = group_tags(tag_types['results'], bookmark['tags']) if 'tags' in bookmark else []
			return render(request, 'bookmark_form.html', {
				'rating_range': [1,2,3,4,5],
				'bookmark': bookmark, 
				'tags': tags})
		else:
			messages.add_message(request, messages.ERROR, 'You must log in to perform this action.')	
			return redirect('/login')


def delete_bookmark(request, bookmark_id):
	response = do_delete(f'api/bookmarks/{bookmark_id}/', request)
	if response[1] == 204:
		messages.add_message(request, messages.SUCCESS, 'Bookmark deleted.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to delete this bookmark.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while deleting this bookmark. Please contact your administrator.')	
	return redirect('/')

def log_in(request):
	if request.method == 'POST':
		user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
		if user is not None:
			login(request, user)
			messages.add_message(request, messages.SUCCESS, 'Login successful.')	
			refer = request.POST.get('referrer') if request.POST.get('referrer') is not None and '/login' not in request.POST.get('referrer') and '/register' not in request.POST.get('referrer') and '/reset' not in request.POST.get('referrer') else '/'
			return redirect(refer)
		else:
			messages.add_message(request, messages.ERROR, 'Login unsuccessful. Please try again.')
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
			messages.add_message(request, messages.SUCCESS, 'Login successful.')	
			refer = request.POST.get('referrer') if request.POST.get('referrer') is not None and '/login' not in request.POST.get('referrer') and '/register' not in request.POST.get('referrer') else '/'
			return redirect(refer)
		else:
			messages.add_message(request, messages.ERROR, 'Login unsuccessful. Please try again.')
			return redirect('/login')
	else:
		if 'HTTP_REFERER' in request.META:
			return render(request, 'login.html', {'referrer': request.META['HTTP_REFERER']})
		else:
			return render(request, 'login.html', {'referrer': '/'})

def register(request):
	if request.method == 'POST':
		response = do_post(f'api/users/', request, data=request.POST)
		if response[1] == 200 or response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Registration successful!')		
			return redirect('/login')
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'Registration is not permitted at this time. Please contact site admin.')				
			return redirect('/')
		else:
			messages.add_message(request, messages.ERROR, 'Registration unsuccessful. Please try again.')
			return redirect('/login')
	else:			
		return render(request, 'register.html', {})

def log_out(request):
	logout(request)
	messages.add_message(request, messages.SUCCESS, 'Logout successful.')		
	return redirect(request.META['HTTP_REFERER'])

@require_http_methods(["GET"])
def work(request, pk):
	chapter_offset = int(request.GET.get('offset', 0))
	view_full = request.GET.get('view_full', False)
	work_types = do_get(f'api/worktypes', request)[0]
	is_draft = request.GET.get('draft')
	url = f'api/works/{pk}/'
	work = do_get(url, request)[0]
	tag_types = do_get(f'api/tagtypes', request)[0]
	tags = group_tags(tag_types['results'], work['tags']) if 'tags' in work else {}	
	chapter_url_string = f'api/works/{pk}/chapters{"?limit=1" if view_full is False else ""}'
	if chapter_offset > 0:
		chapter_url_string = f'{chapter_url_string}&offset={chapter_offset}'
	chapter_response = do_get(chapter_url_string, request)[0]
	user_can_comment = (work['comments_permitted'] and (work['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in work else False
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	scroll_comment_id = request.GET['scrollCommentId'] if'scrollCommentId' in request.GET else None
	chapters = []
	for chapter in chapter_response['results']:
		if 'id' in chapter:
			chapter_comments = do_get(f"api/chapters/{chapter['id']}/comments", request)[0]
			chapter['post_action_url'] = f"/works/{pk}/chapters/{chapter['id']}/comments/new?offset={chapter_offset}"
			chapter['edit_action_url'] = f"""/works/{pk}/chapters/{chapter['id']}/comments/edit?offset={chapter_offset}"""
			chapter['comments'] = chapter_comments
			chapters.append(chapter)
	return render(request, 'work.html', {'work_types': work_types['results'], 
		'work': work,
		'user_can_comment': user_can_comment,
		'scroll_comment_id': scroll_comment_id, 
		'expand_comments': expand_comments,
		'id': pk,
		'tags': tags,
		'view_full': view_full,
		'root': settings.ALLOWED_HOSTS[0],
		'chapters': chapters,
		'chapter_offset': chapter_offset,
		'next_chapter': settings.ALLOWED_HOSTS[0] + '/works/'+str(pk)+'?offset='+str(chapter_offset + 1) if 'next' in chapter_response and chapter_response['next'] else None,
		'previous_chapter': settings.ALLOWED_HOSTS[0] + '/works/'+str(pk)+'?offset='+str(chapter_offset - 1)  if 'previous' in chapter_response and chapter_response['previous'] else None,})

def render_comments(request, work_id, chapter_id):
	limit = request.GET.get('limit', '')
	offset = request.GET.get('offset', '')
	chapter_offset = request.GET.get('chapter_offset', '')
	comments = do_get(f'api/chapters/{chapter_id}/comments?limit={limit}&offset={offset}', request)[0]
	post_action_url = f"/works/{work_id}/chapters/{chapter_id}/comments/new?offset={chapter_offset}"
	edit_action_url = f"""/works/{work_id}/chapters/{chapter_id}/comments/edit?offset={chapter_offset}"""
	return render(request, 'chapter_comments.html', {
		'comments': comments['results'], 
		'chapter_offset': chapter_offset,
		'chapter': {'id': chapter_id}, 
		'work': {'id': work_id},
		'post_action_url': post_action_url,
		'edit_action_url': edit_action_url})

def render_bookmark_comments(request, pk):
	limit = request.GET.get('limit', '')
	offset = request.GET.get('offset', '')
	comments = do_get(f'api/bookmarks/2/comments?limit={limit}&offset={offset}', request)[0]
	post_action_url = f"/bookmarks/{pk}/comments/new"
	edit_action_url = f"""/bookmarks/{pk}/comments/edit"""
	return render(request, 'bookmark_comments.html', {
		'comments': comments['results'], 
		'bookmark': {'id': pk},
		'post_action_url': post_action_url,
		'edit_action_url': edit_action_url})

def create_chapter_comment(request, work_id, chapter_id):
	if request.method == 'POST':
		comment_dict = request.POST.copy()
		offset_url = int(request.GET.get('offset', 0))
		if request.user.is_authenticated:
			comment_dict["user"] = str(request.user)
		else:
			comment_dict["user"] = None
		response = do_post(f'api/comments/', request, data=comment_dict)
		comment_id = response[0]['id'] if 'id' in response[0] else None
		if response[1] == 200 or response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Comment posted.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to post this comment.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while posting this comment. Please contact your administrator.')	
		return redirect(f"/works/{work_id}/?expandComments=true&scrollCommentId={comment_id}&offset={offset_url}")

def edit_chapter_comment(request, work_id, chapter_id):
	if request.method == 'POST':
		comment_dict = request.POST.copy()
		offset_url = int(request.GET.get('offset', 0))
		if request.user.is_authenticated:
			comment_dict["user"] = str(request.user)
		else:
			comment_dict["user"] = None
		response = do_patch(f"api/comments/{comment_dict['id']}/", request, data=comment_dict)
		if response[1] == 200 or response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Comment edited.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to post this comment.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while posting this comment. Please contact your administrator.')	
		return redirect(f"/works/{work_id}/?expandComments=true&scrollCommentId={comment_dict['id']}&offset={offset_url}")
	else:
		messages.add_message(request, messages.ERROR, 'Invalid URL.')	
		return redirect(f'/works/{work_id}')

def delete_chapter_comment(request, work_id, chapter_id, comment_id):
	response = do_delete(f'api/comments/{comment_id}/', request)
	if response[1] == 204:
		messages.add_message(request, messages.SUCCESS, 'Comment deleted.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to delete this comment.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while deleting this comment. Please contact your administrator.')	
	return redirect('/works/'+str(work_id))

def create_bookmark_comment(request, pk):
	if request.method == 'POST':
		comment_dict = request.POST.copy()
		if request.user.is_authenticated:
			comment_dict["user"] = str(request.user)
		else:
			comment_dict["user"] = None
		response = do_post(f'api/bookmarkcomments/', request, data=comment_dict)
		comment_id = response[0]['id'] if 'id' in response[0] else None
		if response[1] == 200 or response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Comment posted.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to post this comment.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while posting this comment. Please contact your administrator.')	
		return redirect(f"/bookmarks/{pk}/?expandComments=true&scrollCommentId={comment_id}")

def edit_bookmark_comment(request, pk):
	if request.method == 'POST':
		comment_dict = request.POST.copy()
		if request.user.is_authenticated:
			comment_dict["user"] = str(request.user)
		else:
			comment_dict["user"] = None
		response = do_put(f"api/bookmarkcomments/{comment_dict['id']}/", request, data=comment_dict)
		if response[1] == 200 or response[1] == 201:
			messages.add_message(request, messages.SUCCESS, 'Comment edited.')	
		elif response[1] == 403:
			messages.add_message(request, messages.ERROR, 'You are not authorized to post this comment.')	
		else:
			messages.add_message(request, messages.ERROR, 'An error has occurred while posting this comment. Please contact your administrator.')	
		return redirect(f"/bookmarks/{pk}/?expandComments=true&scrollCommentId={comment_dict['id']}")
	else:
		messages.add_message(request, messages.ERROR, '404 Page Not Found')	
		return redirect(f'/bookmarks/{pk}')

def delete_bookmark_comment(request, pk, comment_id):
	response = do_delete(f'api/bookmarkcomments/{comment_id}/', request)
	if response[1] == 204:
		messages.add_message(request, messages.SUCCESS, 'Comment deleted.')	
	elif response[1] == 403:
		messages.add_message(request, messages.ERROR, 'You are not authorized to delete this comment.')	
	else:
		messages.add_message(request, messages.ERROR, 'An error has occurred while deleting this comment. Please contact your administrator.')	
	return redirect('/bookmarks/'+str(pk))

def bookmarks(request):	
	response = do_get(f'api/bookmarks/', request, params=request.GET)[0]
	bookmarks = response['results']
	previous_param = response['prev_params']
	next_param = response['next_params']
	bookmarks = get_object_tags(bookmarks, request)
	return render(request, 'bookmarks.html', {
		'bookmarks': bookmarks, 
		'rating_range': [1,2,3,4,5],
		'next': f"/bookmarks/{next_param}" if next_param is not None else None,
		'previous': f"/bookmarks/{previous_param}" if previous_param is not None else None})

def bookmark(request, pk):
	get_url = f'api/bookmarks/{pk}/draft' if request.GET.get('draft') == "True" else f'api/bookmarks/{pk}'
	bookmark = do_get(get_url, request)[0]
	comments = do_get(f'api/bookmarks/{pk}/comments', request)[0]
	bookmark['post_action_url'] = f"/bookmarks/{pk}/comments/new"
	bookmark['edit_action_url'] = f"""/bookmarks/{pk}/comments/edit"""
	expand_comments = 'expandComments' in request.GET and request.GET['expandComments'].lower() == "true"
	scroll_comment_id = request.GET['scrollCommentId'] if'scrollCommentId' in request.GET else None
	user_can_comment = (bookmark['comments_permitted'] and (bookmark['anon_comments_permitted'] or request.user.is_authenticated)) if 'comments_permitted' in bookmark else False
	return render(request, 'bookmark.html', {
		'bookmark': bookmark, 
		'scroll_comment_id': scroll_comment_id, 
		'expand_comments': expand_comments, 
		'user_can_comment': user_can_comment, 
		'rating_range': [1,2,3,4,5], 
		'work': bookmark['work'] if 'work' in bookmark else {}, 
		'comments': comments})

def works_by_tag(request, pk):
	tagged_works = do_get(f'api/tags/{pk}/works', request)[0]
	tagged_bookmarks = do_get(f'api/tags/{pk}/bookmarks', request)[0]
	return render(request, 'tag_results.html', {'tag_id': pk, 'works': tagged_works, 'bookmarks': tagged_bookmarks['results']})

def works_by_tag_next(request, tag_id):
	if 'next' in request.GET:
		next_url = request.GET.get('next', '')
	else:
		next_url = request.GET.get('previous', '')
	offset_url = request.GET.get('offset', '')
	works = do_get(f'{next_url}&offset={offset_url}', request)[0]
	return render(request, 'paginated_works.html', {'works': works, 'tag_id': tag_id})

def upload_file(request):
	if request.method == 'POST':
		# todo
		# send fic uuid + chapter id
		# directory structure: media/uuid/chapter_id/files
		# save file, return location
		# location client-side in audio_url variable
		file_helpers.handle_uploaded_file(request.FILES['files[]'], request.FILES['files[]'].name)
		return redirect('/')
	return render(request, 'upload.html')