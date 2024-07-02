from search.models import SavedSearch
from .api_utils import do_get
from django.conf import settings
from core.utils import convert_boolean


def set_user_data(request):
    css_mode = request.session.get('css_mode')
    saved_searches = []
    if request.user.is_authenticated:
        request_url = f"api/users/{request.user.id}/"
        response = do_get(request_url, request).response_data
        saved_searches = do_get(f"api/users/{request.user.username}/savedsearches", request).response_data.get('results', [])
        if 'has_notifications' in response:
            has_notifications = response['has_notifications']
            request.session['has_notifications'] = has_notifications
        else:
            request.session['has_notifications'] = False
    else:
        request.session['has_notifications'] = False
    request_url = f"api/contentpages/"
    response = do_get(request_url, request).response_data
    oc_settings = do_get(f'api/settings', request).response_data
    settings_dict = {
        x['name'].replace(' ', ''): x['value'] if x['value'].lower() != 'true' and x['value'].lower() != 'false' else (
            convert_boolean(x['value'])) for x in oc_settings['results']} if 'results' in oc_settings else {}
    announcements = do_get(f'api/adminannouncements/active', request).response_data
    announcements = [x for x in announcements.get('results', []) if
                     not request.COOKIES.get(f'dismiss_announcement_{x["id"]}')]

    return {
        'css_mode': css_mode if css_mode is not None else None,
        'content_pages': response.get('results', {}),
        'captcha_site_key': settings.CAPTCHA_SITE_KEY,
        'settings': settings_dict,
        'admin_announcements': announcements,
        'idx_saved_searches': saved_searches
    }
