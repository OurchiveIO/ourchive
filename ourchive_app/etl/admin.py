from django.contrib import admin
from etl.models import WorkImport, ObjectMapping, AdditionalMapping
from .ao3 import work_import as importer

def process_work_import(work_import):
    importer = importer.WorkImport()
    importer.get_single_work(work_import.work_id)


@admin.action(description="Process unprocessed imports")
def process_imports(modeladmin, request, queryset):
    for work_import in queryset:
        process_work_import(work_import)

class WorkImportAdmin(admin.ModelAdmin):
    list_display = ('id', 'work_id', 'job_uid', 'job_success', 'job_finished', 'created_on', 'job_processing', 'user')
    # actions = [process_imports]

class ObjectMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'object_type', 'origin_field', 'destination_field')
    search_fields = ('destination_field', 'object_type')


class AdditionalMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_value', 'destination_object', 'destination_type', 'destination_value')
    search_fields = ('original_value', 'destination_object', 'destination_type')


admin.site.register(WorkImport, WorkImportAdmin)
admin.site.register(ObjectMapping, ObjectMappingAdmin)
admin.site.register(AdditionalMapping, AdditionalMappingAdmin)
