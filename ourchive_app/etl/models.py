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

    def __repr__(self):
        return '<ObjectMapping: {}>'.format(self.id)

    def __str__(self):
        return f"{self.origin_field} to {self.destination_field} for {self.object_type}"
