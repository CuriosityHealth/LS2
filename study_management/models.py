from django.db import models
from django.utils import timezone

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import password_validation
from .settings import PARTICIPANT_ACCOUNT_GENERATOR_PASSWORD_VALIDATORS
from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password,
)
import string
import secrets

from django.db.models import F

from django.core.exceptions import ValidationError

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from fernet_fields import EncryptedTextField
from cryptography.fernet import InvalidToken
import uuid
import arrow

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your models here.
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
            datapoint = Datapoint.objects.filter(study_uuid=self.uuid).latest('ap_source_creation_date_time')
            return datapoint.ap_source_creation_date_time
        except Datapoint.DoesNotExist:
            return None
        except InvalidToken:
            return None

    def last_datapoint_submission_date_string(self):
        date = self.last_datapoint_submission_date()
        if date:
            return arrow.get(date).humanize()
        else:
            return None


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
            datapoint = Datapoint.objects.filter(participant_uuid=self.uuid).latest('ap_source_creation_date_time')
            return datapoint.ap_source_creation_date_time
        except Datapoint.DoesNotExist:
            return None
        except InvalidToken:
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
    participant_uuid = models.UUIDField(editable=False, db_index=True)
    study_uuid = models.UUIDField(editable=False, db_index=True)
    created_date_time = models.DateTimeField(auto_now_add=True)
    schema_namespace = models.CharField(max_length=64)
    schema_name = models.CharField(max_length=32)
    schema_version_major = models.PositiveSmallIntegerField()
    schema_version_minor = models.PositiveSmallIntegerField()
    schema_version_patch = models.PositiveSmallIntegerField()
    ap_source_name = models.CharField(max_length=128)
    ap_source_creation_date_time = models.DateTimeField()
    ap_source_modality = models.CharField(max_length=32)
    metadata = EncryptedTextField(default=None, null=True, blank=True)
    body = EncryptedTextField()

    def __str__(self):
        return str(self.uuid)

    def schema_string(self):
        version = self.schema_version_string()
        return f'{self.schema_namespace}:{self.schema_name}:{version}'

    def schema_version_string(self):
        return f'{self.schema_version_major}.{self.schema_version_minor}.{self.schema_version_patch}'

class PasswordChangeEvent(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=255)
    encoded_password = models.CharField(max_length=100)

class LoginTimeout(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    disable_until = models.DateTimeField()
    username = models.CharField(max_length=255, null=True, blank=True)
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)

    def login_disabled(self):
        now = timezone.now()
        return now <= self.disable_until

class ParticipantAccountGenerator(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    study = models.OneToOneField(Study, on_delete=models.PROTECT)
    generator_password = models.CharField(max_length=128)
    _generator_password = None

    username_prefix = models.CharField(default='', blank=True, max_length=16)
    username_suffix = models.CharField(default='', blank=True, max_length=16)
    username_random_character_length = models.PositiveSmallIntegerField(default=16)
    ## random character alphabet is hex

    password_min_length = models.PositiveSmallIntegerField(default=16)
    password_max_length = models.PositiveSmallIntegerField(default=16)

    number_of_participants_created = models.PositiveSmallIntegerField(default=0)
    max_participants_to_create = models.PositiveSmallIntegerField(default=0)

    def can_generate_participant_account(self):
        return self.is_active and self.number_of_participants_created < self.max_participants_to_create

    def generate_participant(self):

        username = self.generate_username()
        password = self.generate_password()

        logger.debug(username)
        logger.debug(password)

        try:
            user = User(username=username)
            password_validation.validate_password(password, user=user)
            user.set_password(password)
            user.full_clean()
            user.save()
        except ValidationError as e:
            logger.error(e)
            return None

        logger.debug(user)

        try:
            participant = Participant(label=username, user=user, study=self.study)
        except Study.DoesNotExist:
            return None

        try:
            participant.full_clean()
            participant.save()
        except ValidationError as e:
            user.delete()
            return None

        self.number_of_participants_created = F('number_of_participants_created') + 1
        self.save()

        logger.debug(participant)
        return (username, password)

    def generate_username(self):
        alphabet = string.digits + 'ABCDEF'
        size = self.username_random_character_length
        random_chars = ''.join(secrets.choice(alphabet) for _ in range(size))
        return self.username_prefix + random_chars + self.username_suffix

    def generate_password(self):
        alphabet = string.digits + string.ascii_letters
        size_difference = self.password_max_length - self.password_min_length
        size = secrets.randbelow(size_difference + 1) + self.password_min_length
        return ''.join(secrets.choice(alphabet) for _ in range(size))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self._generator_password is not None:
            password_validation.password_changed(self._generator_password, self, password_validators=PARTICIPANT_ACCOUNT_GENERATOR_PASSWORD_VALIDATORS)
            self._generator_password = None

    def set_password(self, raw_password):
        self.generator_password = make_password(raw_password)
        self._generator_password = raw_password

    def check_password(self, raw_password):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            # Password hash upgrades shouldn't be considered password changes.
            self._generator_password = None
            self.save(update_fields=["generator_password"])
        return check_password(raw_password, self.generator_password, setter)
