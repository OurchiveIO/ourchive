from .api_utils import do_get
from django.conf import settings
from api.utils import convert_boolean


def set_style(request):
    css_mode = request.session.get('css_mode')
    return {
        'css_mode': css_mode if css_mode is not None else None
    }


def set_has_notifications(request):
    if request.user.is_authenticated:
        request_url = f"api/users/{request.user.id}/"
        response = do_get(request_url, request).response_data
        if 'has_notifications' in response:
            has_notifications = response['has_notifications']
            request.session['has_notifications'] = has_notifications
        else:
            request.session['has_notifications'] = False
    else:
        request.session['has_notifications'] = False
    return {}


def set_content_pages(request):
    request_url = f"api/contentpages/"
    response = do_get(request_url, request).response_data
    return {'content_pages': response['results']} if 'results' in response else {}


def set_captcha(request):
    return {'captcha_site_key': settings.CAPTCHA_SITE_KEY}


def load_settings(request):
    settings = do_get(f'api/settings', request).response_data
    settings_dict = {x['name'].replace(' ', ''): x['value'] if x['value'].lower() != 'true' and x['value'].lower() != 'false' else (convert_boolean(x['value'])) for x in settings['results']} if 'results' in settings else {}
    return {'settings': settings_dict}
