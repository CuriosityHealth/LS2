from django.contrib.auth.hashers import BCryptSHA256PasswordHasher
from . import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext as _

# Note that Django increases these work factors with new versions
# Therefore, we will base our work factor off of the default
# bcrypt hasher implementation as to always stay ahead
# https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#increasing-the-work-factor
class StrongBCryptSHA256PasswordHasher(BCryptSHA256PasswordHasher):
    if settings.ADDITIONAL_BCRYPT_ROUNDS < 0:
        raise ImproperlyConfigured(
            _("ADDITIONAL_BCRYPT_ROUNDS must be greater than 0")
        )
    rounds = BCryptSHA256PasswordHasher.rounds + settings.ADDITIONAL_BCRYPT_ROUNDS
