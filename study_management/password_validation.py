from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import check_password, make_password, is_password_usable
from django.core.exceptions import ImproperlyConfigured
from .models import PasswordChangeEvent

class ReusedPasswordValidator:

    max_generations_to_save = 12

    def __init__(self, min_generations=3):
        if min_generations > self.max_generations_to_save:
            raise ImproperlyConfigured(
                _(f'The number of generations to check {min_generations} is too \
high. It must be less than or equal to {self.max_generations_to_save}')
            )

        self.min_generations = min_generations


    def validate(self, password, user=None):

        if not user:
            raise AssertionError()
            return

        # get n=min_generations most recent password_change_events for this user
        password_change_events = PasswordChangeEvent.objects.filter(user=user).order_by('-created_date')[:self.min_generations]
        for event in password_change_events:
            if check_password(password, event.encoded_password):
                raise ValidationError(
                    _("You've used this password recently"),
                    code='recently_used_password',
                )

        pass

    def get_help_text(self):
        return _(
            "You cannot select a password that you've used within the last %(min_generations)d times you've changed your password."
            % {'min_generations': self.min_generations}
        )

    def password_changed(self, password, user=None):
        encoded_password = make_password(password)
        password_change_event = PasswordChangeEvent.objects.create(encoded_password=encoded_password, user=user)
