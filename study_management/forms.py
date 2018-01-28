from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django import forms
from .utils import should_disable_login, get_client_ip, password_age_is_valid, is_researcher
from easyaudit.models import LoginEvent
from . import settings

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
        logger.info(f'Confirming that {user} is allowed to log in')
        if not password_age_is_valid(user):
            raise forms.ValidationError(
                f'PermissionDenied: Password too old!!',
                code='password_age'
            )


        if not is_researcher(user):
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

    def clean(self):

        ## check for timeout
        username = self.cleaned_data.get('username')

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
