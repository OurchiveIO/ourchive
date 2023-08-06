from django.contrib import admin
from etl.models import WorkImport, ObjectMapping
from .ao3 import work_import as importer

def process_work_import(work_import):
    importer = importer.WorkImport()
    importer.get_single_work(work_import.work_id)


@admin.action(description="Process unprocessed imports")
def process_imports(modeladmin, request, queryset):
    for work_import in queryset:
        process_work_import(work_import)

class WorkImportAdmin(admin.ModelAdmin):
    actions = [process_imports]

class ObjectMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'object_type', 'origin_field', 'destination_field')
    search_fields = ('destination_field', 'object_type')

admin.site.register(WorkImport, WorkImportAdmin)
admin.site.register(ObjectMapping, ObjectMappingAdmin)
