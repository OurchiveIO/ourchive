import requests
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)


def get_headers(request):
	headers = {}
	headers['X-CSRFToken'] = request.COOKIES['csrftoken'] if 'csrftoken' in request.COOKIES else None
	headers['content-type'] = 'application/json'
	headers['Origin'] = f'{settings.API_PROTOCOL}{settings.ALLOWED_HOSTS[0]}'
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
	response = requests.post(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request))
	return get_results(response)


def do_put(url, request, data={}):
	return get_results(requests.put(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request)))


def do_delete(url, request):
	return get_results(requests.delete(append_root_url(url), cookies=request.COOKIES, headers=get_headers(request)))


def do_get(url, request, params={}):
	response = requests.get(append_root_url(url), params=params, cookies=request.COOKIES, headers=get_headers(request))
	return get_results(response)
