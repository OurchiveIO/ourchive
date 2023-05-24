from django.contrib import admin
from api.models import TagType, WorkType, NotificationType, OurchiveSetting, ContentPage

admin.site.register(TagType)
admin.site.register(WorkType)
admin.site.register(NotificationType)
admin.site.register(OurchiveSetting)
admin.site.register(ContentPage)
