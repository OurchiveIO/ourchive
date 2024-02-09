from django.contrib import admin
from api.models import User, TagType, WorkType, NotificationType, OurchiveSetting, \
    ContentPage, Tag, Invitation, AttributeType, AttributeValue, UserReportReason, \
    UserReport, UserSubscription, AdminAnnouncement
from django.db import models
from django.forms.widgets import Input
from django.core.mail import send_mail
from django.conf import settings
from django.forms import ModelForm, ChoiceField


class RichTextEditorWidget(Input):
    template_name = "admin/rich_text_widget.html"


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'display_text', 'tag_type')
    search_fields = ('text', 'display_text', 'tag_type__label')


class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'attribute_type')
    search_fields = ('name', 'attribute_type__name')


class AttributeTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'allow_on_work', 'allow_on_user', 'allow_on_chapter', 'allow_on_bookmark', 'allow_multiselect')
    search_fields = ('name', 'display_name', 'sort_order')


def send_invite_email(invitation, approved=False):
    if invitation.token_used is False and (approved or invitation.approved):
        send_mail(
            "Your Ourchive invitation",
            f"Your invite request has been approved. Click this link to register: {settings.API_PROTOCOL}{invitation.register_link}",
            settings.DEFAULT_FROM_EMAIL,
            [invitation.email],
            fail_silently=False,
        )


@admin.action(description="Approve selected invitations")
def approve_invitations(modeladmin, request, queryset):
    for invitation in queryset:
        send_invite_email(invitation, True)
        invitation.approved = True
        invitation.save()


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'approved', 'join_reason', 'token_expiration', 'token_used')
    search_fields = ('text', 'tag_type__label')
    actions = [approve_invitations]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        send_invite_email(obj)


class ContentPageAdmin(admin.ModelAdmin):
    change_form_template = "admin/rich_text_content_page.html"
    formfield_overrides = {
        models.TextField: {"widget": RichTextEditorWidget},
    }
    readonly_fields = ["id"]
    list_display = ('name', 'id', 'order')


SETTING_VALUE_CHOICES = [
    [('true', 'True'),('false', 'False')],
    {
        'Search Provider': [('POSTGRES', 'Database')],
        'Invite Queue Limit': [('10', '10'), ('20', '20'), ('50', '50'), ('100', '100')],
        'Rating Star Count': [
            ('1', '1'), ('2', '2'),('3', '3'),('4', '4'),('5', '5'),
            ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10')
        ]
    }

]


class SettingsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            choices = []
            if self.instance.valtype == 'truefalse':
                choices = [x for x in SETTING_VALUE_CHOICES[0]]
                self.fields['value'] = ChoiceField(choices=choices)
            if self.instance.valtype == 'choice':
                choices = SETTING_VALUE_CHOICES[1][self.instance.name]
                self.fields['value'] = ChoiceField(choices=choices)


class OurchiveSettingAdmin(admin.ModelAdmin):
    form = SettingsForm
    exclude = ('valtype',)
    readonly_fields = ('name', )
    fields = ('name', 'value',)
    list_display = ('id', 'name', 'value', 'uid')


@admin.action(description="Allow selected users to upload images")
def allow_image_upload(modeladmin, request, queryset):
    for user in queryset:
        user.can_upload_images = True
        user.save()


@admin.action(description="Allow selected users to upload audio")
def allow_audio_upload(modeladmin, request, queryset):
    for user in queryset:
        user.can_upload_audio = True
        user.save()


@admin.action(description="Allow selected users to upload preferred export files")
def allow_export_upload(modeladmin, request, queryset):
    for user in queryset:
        user.can_upload_export_files = True
        user.save()


@admin.action(description="Allow selected users to upload all files")
def allow_all_upload(modeladmin, request, queryset):
    for user in queryset:
        user.can_upload_export_files = True
        user.can_upload_audio = True
        user.can_upload_images = True
        user.save()


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'id', 'email', 'is_staff', 'can_upload_images', 'can_upload_audio', 'can_upload_export_files')
    actions = [allow_audio_upload, allow_image_upload, allow_export_upload, allow_all_upload]


@admin.action(description="Resolve selected reports")
def resolve_reports(modeladmin, request, queryset):
    for report in queryset:
        report.resolved = True
        report.save()


class UserReportAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'resolved')
    actions = [resolve_reports]


class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed_user', 'subscribed_to_bookmark', 'subscribed_to_collection')


class AdminAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content')


class TagTypeAdmin(admin.ModelAdmin):
    list_display = ('label', 'sort_order', 'filterable', 'show_in_aggregate')


class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name', 'sort_order')


admin.site.register(TagType, TagTypeAdmin)
admin.site.register(WorkType, WorkTypeAdmin)
admin.site.register(NotificationType)
admin.site.register(OurchiveSetting, OurchiveSettingAdmin)
admin.site.register(ContentPage, ContentPageAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(AttributeType, AttributeTypeAdmin)
admin.site.register(AttributeValue, AttributeValueAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserReportReason)
admin.site.register(UserReport, UserReportAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(AdminAnnouncement, AdminAnnouncementAdmin)
