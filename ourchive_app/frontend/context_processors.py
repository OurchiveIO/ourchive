def set_style(request):
    css_mode = request.session.get('css_mode')
    return {
        'css_mode': css_mode if css_mode is not None else "light",
    }