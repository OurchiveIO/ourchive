from .api_utils import do_get
from django.conf import settings


def set_style(request):
    css_mode = request.session.get('css_mode')
    return {
        'css_mode': css_mode if css_mode is not None else "light"
    }


def set_has_notifications(request):
    if request.user.is_authenticated:
        request_url = f"api/users/{request.user.id}/"
        response = do_get(request_url, request)[0]
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
    response = do_get(request_url, request)[0]
    return {'content_pages': response['results']}


def set_captcha(request):
    return {'captcha_site_key': settings.CAPTCHA_SITE_KEY}


def load_settings(request):
    settings = do_get(f'api/settings', request)[0]
    settings_dict = {x['name'].replace(' ', ''): x['value'] for x in settings['results']}
    return {'settings': settings_dict}
