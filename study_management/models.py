from django.db import models
from django.utils import timezone

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import password_validation
from .settings import PARTICIPANT_ACCOUNT_GENERATOR_PASSWORD_VALIDATORS, PASSWORD_AGE_LIMIT_MINUTES, PASSWORD_AGE_WARN_MINUTES
from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password,
)

from django.template import Context, Template

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

from datetime import timedelta

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

class LDAPUserToResearcherConverter(models.Model):
    ldap_username = models.CharField(max_length=50)
    studies = models.ManyToManyField(Study, blank=True)
    converted = models.BooleanField(default=False)

    def __str__(self):
        return self.ldap_username

    def convert_to_researcher(self, user):

        logger.debug(self)
        studies = self.studies.all()
        logger.debug(studies)
        if self.converted:
            logger.error("Already converted")
            return None

        researcher = Researcher(user=user)

        try:
            researcher.full_clean()
            researcher.save()
            researcher.studies.set(self.studies.all())
            researcher.save()
        except ValidationError as e:
            logger.error(e)
            researcher.delete()
            user.delete()
            return None

        self.converted = True
        self.save()
        return researcher

class Researcher(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    #we should never change this!
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    studies = models.ManyToManyField(Study, blank=True)

    def __str__(self):
        return self.user.username

    def must_change_password(self):

        if self.is_ldap_user():
            return False

        try:
            count = self.user.passwordchangeevent_set.count()
            return count <= 1
        except Datapoint.DoesNotExist:
            return None

    def is_ldap_user(self):

        # logger.info(f'ldap username is {self.user.ldap_username}')
        logger.info(f'check for ldap username for user {self.user}')
        logger.info(f'{getattr(self.user, "ldap_username", None)}')
        return getattr(self.user, "ldap_username", None) != None

    def password_age_is_valid(self):

        #make sure time since latest password change event is less than PASSWORD_AGE_LIMIT_MINUTES
        logger.info(f'checking password age')
        try:
            password_change_event = PasswordChangeEvent.objects.filter(
                user=self.user,
            ).latest('created_date')

            age_limit = timedelta(minutes=PASSWORD_AGE_LIMIT_MINUTES)
            age = timezone.now() - password_change_event.created_date
            logger.info(f'password age limit is {age_limit}')
            logger.info(f'password age is {age}')
            return age < age_limit

        except PasswordChangeEvent.DoesNotExist:
            logger.info(f'Password change event does not exist')
            return False

    def should_warn_about_password_age(self):

        # warn if time since latest password change event is more than PASSWORD_AGE_WARN_MINUTES
        try:
            password_change_event = PasswordChangeEvent.objects.filter(
                user=self.user,
            ).latest('created_date')

            age_warn = timedelta(minutes=PASSWORD_AGE_WARN_MINUTES)
            age = timezone.now() - password_change_event.created_date
            logger.info(f'password age warn is {age_warn}')
            logger.info(f'password age is {age}')
            return age > age_warn

        except PasswordChangeEvent.DoesNotExist:
            return False

class ParticipantAuthToken(models.Model):

    """
    The user  authorization token based on the Django Rest token.
    The main difference is here that user is not one-to-one, i.e., a user can have muiltiple tokens
    """
    key = models.CharField(_("Key"), max_length=64, primary_key=True)
    user = models.ForeignKey(
        User, related_name='participant_auth_token',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    last_used = models.DateTimeField(_("Last Used"), auto_now_add=True)
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:

        verbose_name = _("Participant Auth Token")
        verbose_name_plural = _("Participant Auth Token")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ParticipantAuthToken, self).save(*args, **kwargs)

    def generate_key(self):
        return secrets.token_hex(32)

    def __str__(self):
        return self.key

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

    study = models.ForeignKey(Study, on_delete=models.PROTECT)
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

    def __str__(self):
        return str(self.uuid)

    ## Throttling
    ## note there is both system wide throttling as well as
    ## generator specific throttling
    ## for system-wide, we would like to prevent a user from brute forcing
    ## uuid or password

    def can_generate_participant_account(self):
        return self.is_active and self.number_of_participants_created < self.max_participants_to_create

    def generate_participant(self):

        username = self.generate_username()
        password = self.generate_password()

        # logger.debug(username)
        # logger.debug(password)

        try:
            user = User(username=username)
            password_validation.validate_password(password, user=user)
            user.set_password(password)
            user.full_clean()
            user.save()
        except ValidationError as e:
            logger.error(e)
            return None

        # logger.debug(user)

        try:
            participant = Participant(label=username, user=user, study=self.study)
        except Study.DoesNotExist:
            logger.error(e)
            user.delete()
            return None

        try:
            participant.full_clean()
            participant.save()
        except ValidationError as e:
            logger.error(e)
            user.delete()
            return None

        self.number_of_participants_created = F('number_of_participants_created') + 1
        self.save()

        # logger.debug(participant)
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

class ParticipantAccountGenerationRequestEvent(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    generator_id = models.UUIDField(blank=True)
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)

class ParticipantAccountGenerationTimeout(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    ## if generator_id is blank, this denotes a global timeout
    generator_id = models.UUIDField(blank=True)
    disable_until = models.DateTimeField()
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)

    def disabled(self):
        now = timezone.now()
        return now <= self.disable_until


class TokenBasedParticipantAccountGenerator(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    study = models.ForeignKey(Study, on_delete=models.PROTECT)

    username_prefix = models.CharField(default='', blank=True, max_length=16)
    username_suffix = models.CharField(default='', blank=True, max_length=16)
    username_random_character_length = models.PositiveSmallIntegerField(default=16)
    ## random character alphabet is hex

    password_min_length = models.PositiveSmallIntegerField(default=16)
    password_max_length = models.PositiveSmallIntegerField(default=16)


    ##Token generation defaults to 64-byte (512-bit) base64 encoded string
    #token format
    ## numerical - typical use case would  be 6-8 digit codes
    ## alphanumeric (uppercase letters only, typical use case would be 6-8 digit alphanum codes)
    ## base64 - typical use case would be 
    NUMERIC = 'NM'
    ALPHANUMERIC = 'AN'
    BASE64 = '64'
    TOKEN_FORMAT_CHOICES = (
        (NUMERIC, 'Numeric'),
        (ALPHANUMERIC, 'Alphanumeric'),
        (BASE64, 'Base64'),
    )

    token_format = models.CharField(
        max_length=2,
        choices=TOKEN_FORMAT_CHOICES,
        default=BASE64,
    )

    #token length
    token_size = models.PositiveSmallIntegerField(default=64)
    #token lifetime
    token_lifetime = models.DurationField()

    #optional url template
    url_template = models.TextField(blank=True)

    def __str__(self):
        return str(self.uuid)

    

    ## Throttling
    ## note there is both system wide throttling as well as
    ## generator specific throttling
    ## for system-wide, we would like to prevent a user from brute forcing
    ## uuid or password

    def can_generate_token(self):
        return self.is_active

    def can_redeem_token(self):
        return self.is_active

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

    def generateTokenString(self):

        size = self.token_size

        ##size^8
        if self.token_format == self.BASE64:
            return secrets.token_urlsafe(size)

        ##size^10
        if self.token_format == self.NUMERIC:
            alphabet = string.digits
            return ''.join(secrets.choice(alphabet) for _ in range(size))

        ##size^36
        if self.token_format == self.ALPHANUMERIC:
            alphabet = string.digits + string.ascii_uppercase
            return ''.join(secrets.choice(alphabet) for _ in range(size))

    def generate_token(self):

        MAX_LOOP_ITERATIONS = 10

        # logger.debug(username)
        # logger.debug(password)

        #check for existing username
        ##default odds of collision are 1/(16^16) * n

        ## check against all users and all tokens
        username = None
        loop_counter = 0
        while(True):

            loop_counter = loop_counter + 1
            if loop_counter > MAX_LOOP_ITERATIONS:
                return None

            username = self.generate_username()
            try:
                user = User.objects.get(username=username)
                continue
            except User.DoesNotExist:
                try:
                    token = ParticipantAccountToken.objects.get(username=username)
                    continue
                except ParticipantAccountToken.DoesNotExist:
                    break 
        
        expiration_date_time = timezone.now() + self.token_lifetime

        ##check for valid token_string collision
        ##Note that for sufficiently small alphabet + length and large token_lifetime + population,
        ##this could actually spend a lot of time in this loop. We would want to prevent this, so maybe add
        ##a max number of iterations in this loop?
        token_string = None
        loop_counter = 0
        while(True):

            loop_counter = loop_counter + 1
            if loop_counter > MAX_LOOP_ITERATIONS:
                return None

            token_string = self.generateTokenString()
            token = ParticipantAccountToken.getValidToken(token=token_string, generator_id=self.uuid)
            if token == None:
                break

        token = ParticipantAccountToken.objects.create(
            token=token_string,
            username=username,
            account_generator=self,
            expiration_date_time=expiration_date_time
        )

        return token

    def generate_participant(self, token):

        username = token.username
        password = self.generate_password()

        # logger.debug(username)
        # logger.debug(password)

        try:
            user = User(username=username)
            password_validation.validate_password(password, user=user)
            user.set_password(password)
            user.full_clean()
            user.save()
        except ValidationError as e:
            logger.error(e)
            return None

        # logger.debug(user)

        try:
            participant = Participant(label=username, user=user, study=self.study)
        except Study.DoesNotExist:
            logger.error(e)
            user.delete()
            return None

        try:
            participant.full_clean()
            participant.save()
        except ValidationError as e:
            logger.error(e)
            user.delete()
            return None

        return (username, password)


class ParticipantAccountToken(models.Model):

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=128)
    username = models.CharField(max_length=50)
    account_generator = models.ForeignKey(TokenBasedParticipantAccountGenerator, on_delete=models.PROTECT)
    created_date_time = models.DateTimeField(auto_now_add=True)
    expiration_date_time = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_date_time = models.DateTimeField(blank=True, null=True)
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.uuid)

    def redacted_token(self):
        if len(self.token) <= 4:
            return "****"

        if len(self.token) <= 8:
            return self.token[0] + "****" + self.token[-1]

        else:
            return self.token[:2] + "****" + self.token[-2:]
        
    def expired(self):
        return self.expiration_date_time < timezone.now()

    def url(self):
        generator = self.account_generator
        if len(generator.url_template) == 0:
            return None
        else:
            template_string = generator.url_template
            context = { 'token': self.token, 'generator_uuid': generator.uuid }
            tpl = Template(template_string)
            rendered = tpl.render(Context(context))
            logger.debug(rendered)
            print(rendered)
            return rendered

    @staticmethod
    def getValidToken(*, token, generator_id):

        try:
            participantAccountToken = ParticipantAccountToken.objects.get(
                token=token, 
                account_generator__uuid=generator_id,
                used=False,
                expiration_date_time__gt=timezone.now(),
                disabled=False
            )

            logger.debug(participantAccountToken)
            return participantAccountToken

        except ParticipantAccountToken.DoesNotExist:
            logger.warn(f'Invalid token')
            return None

    @staticmethod
    def getTokenByUUID(*, token_id, generator_id):

        try:
            participantAccountToken = ParticipantAccountToken.objects.get(
                uuid=token_id, 
                account_generator__uuid=generator_id
            )

            logger.debug(participantAccountToken)
            return participantAccountToken

        except ParticipantAccountToken.DoesNotExist:
            logger.warn(f'Invalid token')
            return None
