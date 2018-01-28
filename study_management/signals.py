from . import settings
from easyaudit.models import LoginEvent
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models.signals import post_save
from .models import LoginTimeout
from .utils import should_disable_login

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def on_login_event(sender, instance, **kwargs):
    # on a failed login, check to see if we should create a login timeout
    if instance.login_type == LoginEvent.FAILED:
        now = timezone.now()
        since_time = timedelta(minutes=settings.LOGIN_RATE_LIMIT_WINDOW_MINUTES)
        earlier = now - since_time

        try:
            failed_login_attempts = LoginEvent.objects.filter(
                username=instance.username,
                remote_ip=instance.remote_ip,
                login_type=LoginEvent.FAILED,
                datetime__gt=earlier,
            )

        except LoginEvent.DoesNotExist:
            return

        logger.info(f'there have been {failed_login_attempts.count()} failed login attempts')
        if failed_login_attempts.count() >= settings.LOGIN_RATE_LIMIT_FAILED_ATTEMPTS and \
            should_disable_login(instance.username, instance.remote_ip) == False:

            logger.info('we should throttle here!!!')
            diable_until = now + timedelta(minutes=settings.LOGIN_RATE_LIMIT_TIMEOUT_MINUTES)
            login_timeout = LoginTimeout.objects.create(
                disable_until=diable_until,
                username=instance.username,
                remote_ip=instance.remote_ip
            )



if settings.LOGIN_RATE_LIMIT_ENABLED:
    post_save.connect(on_login_event, sender=LoginEvent)
