from django.db import models
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
import uuid
import arrow

# Create your models here.
class PublicKeyInfo(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    contents = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.uuid)

class Study(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def summary(self):
        last_datapoint_date = self.last_datapoint_submission_date_string()
        if not last_datapoint_date:
            return "No data collected yet"
        else:
            return f'Last data collected {last_datapoint_date}'

    def last_datapoint_submission_date(self):
        try:
            datapoint = self.datapoint_set.all().latest('ap_source_creation_date_time')
            return datapoint.ap_source_creation_date_time
        except Datapoint.DoesNotExist:
            return None

    def last_datapoint_submission_date_string(self):
        date = self.last_datapoint_submission_date()
        if date:
            return arrow.get(date).humanize()
        else:
            return None

    def latest_configuration(self):
        try:
            return self.configurations.all().latest('created_date')
        except StudyConfiguration.DoesNotExist:
            return None

class StudyConfiguration(models.Model):
    study = models.ForeignKey(Study, on_delete=models.PROTECT, related_name='configurations')
    public_key_info = models.ForeignKey(PublicKeyInfo, on_delete=models.PROTECT, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    encrypt_by_default = models.BooleanField(default=False)
    version = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.study}.{self.version}: {self.created_date}'

class Researcher(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    #we should never change this!
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    studies = models.ManyToManyField(Study, blank=True)

    def __str__(self):
        return self.user.username

    def must_change_password(self):
        try:
            count = self.user.passwordchangeevent_set.count()
            return count <= 1
        except Datapoint.DoesNotExist:
            return None


class Participant(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=50)
    #we should never change this!
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    #We should never change this!
    study = models.ForeignKey(Study, on_delete=models.PROTECT)

    def __str__(self):
        return self.label

    def last_datapoint_submission_date(self):
        try:
            datapoint = self.datapoint_set.all().latest('ap_source_creation_date_time')
            return datapoint.ap_source_creation_date_time
        except Datapoint.DoesNotExist:
            return None

    def last_datapoint_submission_date_string(self):

        date = self.last_datapoint_submission_date()
        if date:
            return arrow.get(date).humanize()
        else:
            return None

## Potentially, we can try to store data in another database, although still postgres
class Datapoint(models.Model):
    uuid = models.UUIDField(unique=True, editable=False)
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT)
    study = models.ForeignKey(Study, on_delete=models.PROTECT)
    created_date_time = models.DateTimeField(auto_now_add=True)
    schema_namespace = models.CharField(max_length=64)
    schema_name = models.CharField(max_length=32)
    schema_version_major = models.PositiveSmallIntegerField()
    schema_version_minor = models.PositiveSmallIntegerField()
    schema_version_patch = models.PositiveSmallIntegerField()
    ap_source_name = models.CharField(max_length=128)
    ap_source_creation_date_time = models.DateTimeField()
    ap_source_modality = models.CharField(max_length=32)
    body = JSONField()

    def __str__(self):
        return str(self.uuid)

    def schema_string(self):
        version = self.schema_version_string()
        return f'{self.schema_namespace}:{self.schema_name}:{version}'

    def schema_version_string(self):
        return f'{self.schema_version_major}.{self.schema_version_minor}.{self.schema_version_patch}'

class PasswordChangeEvent(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    encoded_password = models.CharField(max_length=100)

class LoginTimeout(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    disable_until = models.DateTimeField()
    username = models.CharField(max_length=255, null=True, blank=True)
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)

    def login_disabled(self):
        now = timezone.now()
        return now <= self.disable_until
