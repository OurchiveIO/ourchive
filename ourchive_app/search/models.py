from django.db import models
import uuid
from django.utils import timezone
import core.models


class SavedSearch(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100, blank=False, null=False)
    user = models.ForeignKey(core.models.User, on_delete=models.CASCADE)
    tag_id = models.IntegerField(null=True, blank=True)
    type_id = models.IntegerField(null=True, blank=True)
    attr_id = models.IntegerField(null=True, blank=True)
    languages = models.ManyToManyField('core.Language')
    order_by = models.CharField(max_length=100, blank=True, null=True)
    info_facets = models.CharField(null=True, blank=True)
    include_facets = models.CharField(null=True, blank=True)
    exclude_facets = models.CharField(null=True, blank=True)

    def __repr__(self):
        return '<SavedSearch: {}>'.format(self.id)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['updated_on', 'name']
