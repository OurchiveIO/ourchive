from .api_utils import do_get

def set_style(request):
    css_mode = request.session.get('css_mode')
    return {
        'css_mode': css_mode if css_mode is not None else "light"
    }

def set_has_notifications(request):
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
    return {}