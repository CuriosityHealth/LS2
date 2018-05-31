from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django import forms
from .utils import should_disable_login, get_client_ip, is_researcher
from easyaudit.models import LoginEvent
from . import settings
from .models import ParticipantAccountGenerator
from .settings import PARTICIPANT_ACCOUNT_GENERATOR_PASSWORD_VALIDATORS
from django.utils.translation import gettext, gettext_lazy as _

from django.contrib.auth import password_validation
from django.contrib.auth.forms import ReadOnlyPasswordHashField

UserModel = get_user_model()

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ParticipantCreationForm(UserCreationForm):
    participant_label = forms.CharField(max_length=50)
    class Meta(UserCreationForm.Meta):
        fields = ('username', 'participant_label', 'password1', 'password2',)

class ResearcherAuthenticationForm(AuthenticationForm):

    def confirm_login_allowed(self, user):

        logger.debug(f'Confirming that {user} is allowed to log in')
        if not is_researcher(user):
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

        logger.debug(f'{user} is a researcher')
        researcher = user.researcher
        if researcher.is_ldap_user():
            logger.info(f'{user} is a researcher')
            return

        else:
            logger.info(f'Confirming that {user} is allowed to log in')
            if not researcher.password_age_is_valid():
                raise forms.ValidationError(
                    f'PermissionDenied: Password too old!!',
                    code='password_age'
                )

    def clean(self):

        ## check for timeout
        username = self.cleaned_data.get('username')

        ##TODO: potentially check that username matches format
        ##This could help prevent someone from trying funny business with usernames

        if username is not None and should_disable_login(username, get_client_ip(self.request)):

            user_model = get_user_model()
            login_event = LoginEvent.objects.create(login_type=LoginEvent.FAILED,
                                                    username=username,
                                                    remote_ip=get_client_ip(self.request))

            raise forms.ValidationError(
                f'PermissionDenied: Too Many Login Attempts. Please try again in {settings.LOGIN_RATE_LIMIT_TIMEOUT_MINUTES} minutes.',
                code='too_many_attempts'
            )

        return super().clean()

class ParticipantAccountGeneratorCreationForm(forms.ModelForm):

    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(
        label=_("Generator Password"),
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(password_validators=PARTICIPANT_ACCOUNT_GENERATOR_PASSWORD_VALIDATORS),
    )
    password2 = forms.CharField(
        label=_("Generator Password confirmation"),
        widget=forms.PasswordInput,
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = ParticipantAccountGenerator
        fields = ('study',
            'username_prefix',
            'username_suffix',
            'username_random_character_length',
            'password_min_length',
            'password_max_length',
            'max_participants_to_create')

        # fields = (UserModel.USERNAME_FIELD,)
        # field_classes = {UserModel.USERNAME_FIELD: UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if self._meta.model.USERNAME_FIELD in self.fields:
        #     self.fields[self._meta.model.USERNAME_FIELD].widget.attrs.update({'autofocus': True})

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get('password2')
        if password:
            try:
                logger.debug('validating password')
                logger.debug(PARTICIPANT_ACCOUNT_GENERATOR_PASSWORD_VALIDATORS)
                password_validation.validate_password(password, self.instance, password_validators=PARTICIPANT_ACCOUNT_GENERATOR_PASSWORD_VALIDATORS)
            except forms.ValidationError as error:
                self.add_error('password2', error)

    def save(self, commit=True):
        generator = super().save(commit=False)
        generator.set_password(self.cleaned_data["password1"])
        if commit:
            generator.save()
        return generator

class ParticipantAccountGeneratorChangeForm(forms.ModelForm):

    generator_password = ReadOnlyPasswordHashField(
        label=_("Generator Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user's password, but you can change the password using "
            "<a href=\"{}\">this form</a>."
        ),
    )

    def clean_generator_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["generator_password"]

    class Meta:
        model = ParticipantAccountGenerator
        fields = '__all__'
