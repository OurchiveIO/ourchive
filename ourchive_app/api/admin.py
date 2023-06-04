from django.contrib import admin
from api.models import TagType, WorkType, NotificationType, OurchiveSetting, ContentPage, Tag, Invitation, AttributeType, AttributeValue


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'display_text', 'tag_type')
    search_fields = ('text', 'tag_type__label')


class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'attribute_type')
    search_fields = ('name', 'attribute_type__name')


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'register_link', 'token_expiration', 'token_used')
    search_fields = ('text', 'tag_type__label')


admin.site.register(TagType)
admin.site.register(WorkType)
admin.site.register(NotificationType)
admin.site.register(OurchiveSetting)
admin.site.register(ContentPage)
admin.site.register(Tag, TagAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(AttributeType)
admin.site.register(AttributeValue, AttributeValueAdmin)
