from django.contrib.auth.backends import ModelBackend
from .utils import should_disable_login, get_client_ip
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from .models import LoginTimeout
from django.utils import timezone


class RateLimitedAuthenticationBackend(ModelBackend):

    # the login form is what actually calls the authenticate method of
    # django.contrib.auth. Therefore, we may want to do this
    # we will probably need to pair this with the login form so that there is
    # good info coming back to the user
    def authenticate(self, request, username=None, password=None):

        # check for an active timeout
        if should_disable_login(username, get_client_ip(request)):
            raise PermissionDenied(
                _(f'Too many failed log in attempts.')
            )

        return super().authenticate(request=request, username=username, password=password)
