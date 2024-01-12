from django.db import models
import uuid
from api import models as api


class WorkImport(models.Model):

    __tablename__ = 'workimports'

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    work_id = models.IntegerField()
    job_uid = models.UUIDField()
    job_message = models.TextField()
    job_success = models.BooleanField(default=True)
    job_finished = models.BooleanField(default=False)
    job_processing = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    save_as_draft = models.BooleanField(default=True)
    allow_anon_comments = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)

    user = models.ForeignKey(
        api.User,
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return '<WorkImport: {}>'.format(self.id)


class ChiveExport(models.Model):

    __tablename__ = 'chive_exports'

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    job_message = models.TextField()
    job_success = models.BooleanField(default=True)
    job_finished = models.BooleanField(default=False)
    job_processing = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    export_works = models.BooleanField(default=True)
    export_bookmarks = models.BooleanField(default=True)
    export_collections = models.BooleanField(default=True)

    user = models.ForeignKey(
        api.User,
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return '<ChiveExport: {}>'.format(self.id)


class ObjectMapping(models.Model):
    __tablename__ = 'objectmappings'

    IMPORT_TYPES = [
        ('ao3', 'ao3')
    ]

    OBJECT_TYPES = [
        ('work', 'work'),
        ('chapter', 'chapter'),
        ('work_type', 'work_type')
    ]

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    import_type = models.CharField(max_length=100, choices=IMPORT_TYPES)
    object_type = models.CharField(max_length=100, choices=OBJECT_TYPES)
    origin_field = models.CharField(max_length=100)
    destination_field = models.CharField(max_length=100)
    additional_mappings = models.BooleanField(default=False)

    def __repr__(self):
        return '<ObjectMapping: {}>'.format(self.id)

    def __str__(self):
        return f"{self.origin_field} to {self.destination_field} for {self.object_type}"

class AdditionalMapping(models.Model):
    __tablename__ = 'additionalmappings'

    OBJECT_TYPES = [
        ('tag', 'tag'),
        ('attribute', 'attribute'),
    ]

    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    original_value = models.CharField(max_length=300)
    destination_object = models.CharField(max_length=100, choices=OBJECT_TYPES)
    destination_value = models.CharField(max_length=120)
    destination_type = models.CharField(max_length=200)

    def __repr__(self):
        return '<AdditionalMapping: {}>'.format(self.id)

    def __str__(self):
        return f"{self.original_value} to {self.destination_value} for {self.destination_object}"
