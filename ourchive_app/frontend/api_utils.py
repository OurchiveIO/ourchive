import requests
from django.conf import settings
import logging
import json
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class ResponseInfo():
	status_code = None
	message = None
	type_label = None

	def __init__(self, status_code, message, type_label):
		self.status_code = status_code
		self.message = message
		self.type_label = type_label


class ResponseFull():
	response_data = {}
	response_info = None

	def __init__(self, response_data, response_info):
		self.response_data = response_data
		self.response_info = response_info


def get_headers(request):
	headers = {}
	headers['X-CSRFToken'] = request.COOKIES['csrftoken'] if 'csrftoken' in request.COOKIES else None
	headers['content-type'] = 'application/json'
	headers['Origin'] = f'{settings.API_PROTOCOL}{settings.ROOT_URL}'
	return headers


def append_root_url(url):
	return f"{settings.API_PROTOCOL}{settings.ROOT_URL}/{url}"


def get_200s_message(status_code, object_name, html_obj_name) -> tuple[str, str]:
	if status_code == 200:
		return [_(f"{object_name}(s) updated successfully."), f'{html_obj_name}-update-success']
	elif status_code == 201:
		return [_(f"{object_name}(s) created successfully."), f'{html_obj_name}-create-success']
	elif status_code == 204:
		return [_(f"{object_name}(s) deleted successfully."), f'{html_obj_name}-delete-success']


def get_400s_message(status_code, object_name, html_obj_name, response=None) -> tuple[str, str]:
	if status_code == 400:
		content_json = response.json()
		if 'status_code' in content_json:
			content_json.pop('status_code')
		error_string = ""
		for error in list(content_json):
			if error_string:
				error_string = f"{error_string}; "
			field_error = ""
			for field_error_val in content_json[error]:
				if field_error:
					field_error = f"{field_error}; "
				field_error = f"{field_error}{field_error_val}"
			error_string = f"{error_string}{error}: {field_error}"
		return [_(f"Bad request. Please address the following errors: {error_string}"), f'{html_obj_name}-bad-request-error']
	if status_code == 403:
		return [_(f"You are not authorized to access this {object_name}. Please contact your administrator for more information."), f'{html_obj_name}-unauthorized-error']
	if status_code == 404:
		return [_(f"We could not find this {object_name}. You may not have access to it, or it may not exist."), f"{html_obj_name}-not-found-error"]
	if status_code == 418:
		if response is not None:
			content_json = response.json()
			return[_(content_json['message']), f"{html_obj_name}-validation-error"]
	return [_("An unknown error occurred."), f"{html_obj_name}-unknown-error"]

def get_500s_message(status_code, object_name, html_obj_name) -> tuple[str, str]:
	if status_code == 500:
		return [_(f"An error occurred while accessing this {object_name}. Please contact your administrator for more information."), f"{html_obj_name}-error"]


def get_response_info(response, object_name) -> ResponseInfo:
	status_code = response.status_code
	message = ['', '']
	html_obj_name = object_name.replace(' ', '-').lower()
	if status_code >= 200 and status_code < 400:
		message = get_200s_message(status_code, object_name, html_obj_name)
	if status_code >= 400 and status_code < 500:
		message = get_400s_message(status_code, object_name, html_obj_name, response)
	if status_code >= 500:
		message = get_500s_message(status_code, object_name, html_obj_name)
	return ResponseInfo(status_code, message[0], message[1])


def get_response_data(response) -> dict:
	try:
		return response.json()
	except Exception as e:
		logger.error(f"Error decoding response data: {e}")
		return {}


def get_results(results, object_name='object') -> ResponseFull:
	response_data = {}
	if results.status_code >= 200 and results.status_code < 300:
		response_data = get_response_data(results)
	response_info = get_response_info(results, object_name)
	return ResponseFull(response_data, response_info)


def do_patch(url, request, data={}, object_name='object'):
	return get_results(requests.patch(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request)), object_name)


def do_post(url, request, data={}, object_name='object'):
	response = requests.post(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request))
	return get_results(response, object_name)


def do_external_post(url, data):
	return requests.post(url, data=data)


def do_put(url, request, data={}, object_name='object'):
	return get_results(requests.put(append_root_url(url), data=json.dumps(data), cookies=request.COOKIES, headers=get_headers(request)), object_name)


def do_delete(url, request, object_name='object'):
	return get_results(requests.delete(append_root_url(url), cookies=request.COOKIES, headers=get_headers(request)), object_name)


def do_get(url, request, params={}, object_name='object'):
	response = requests.get(append_root_url(url), params=params, cookies=request.COOKIES, headers=get_headers(request))
	return get_results(response, object_name)


def validate_captcha(request):
	if settings.CAPTCHA_PROVIDER == 'hcaptcha':
		return validate_hcaptcha(request)
	return False


def validate_hcaptcha(request):
	validate_key = request.POST.get(settings.CAPTCHA_PARAM)
	params = {
		"secret": settings.CAPTCHA_SECRET,
		"response": validate_key
	}
	response = do_external_post("https://hcaptcha.com/siteverify", params)
	success = response.json()['success']
	return success
