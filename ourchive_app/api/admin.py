from django.contrib import admin
from api.models import TagType, WorkType, NotificationType, OurchiveSetting

admin.site.register(TagType)
admin.site.register(WorkType)
admin.site.register(NotificationType)
admin.site.register(OurchiveSetting)
