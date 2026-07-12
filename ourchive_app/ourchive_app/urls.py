from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, re_path
from django.conf.urls import include


urlpatterns = [
    path('api/', include('api.urls')),
    path('', include('frontend.urls')),
path(
        'admin/login/',
        lambda r: redirect(
            f"/login/?next=/admin/"
        )
    ),
    path('admin/', admin.site.urls),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
