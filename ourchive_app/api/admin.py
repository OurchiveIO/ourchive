from django.contrib import admin
from api.models import TagType, WorkType, NotificationType, OurchiveSetting, ContentPage, Tag

class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'display_text', 'tag_type')
    search_fields = ('text', 'tag_type__label')

admin.site.register(TagType)
admin.site.register(WorkType)
admin.site.register(NotificationType)
admin.site.register(OurchiveSetting)
admin.site.register(ContentPage)
admin.site.register(Tag, TagAdmin)