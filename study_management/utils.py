from .models import LoginTimeout, PasswordChangeEvent, Researcher, Participant
from django.utils import timezone
from datetime import timedelta
from . import settings

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Returns the IP of the request, accounting for the possibility of being
    behind a proxy.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", None)
    if ip:
        # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
        ip = ip.split(", ")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip

def should_disable_login(username, remote_ip):

    try:

        login_timeout = LoginTimeout.objects.filter(
            username=username,
            remote_ip=remote_ip,
            disable_until__gt=timezone.now()
        ).latest('disable_until')

        if login_timeout != None and login_timeout.login_disabled():
            return True
        else:
            return False

    except LoginTimeout.DoesNotExist:
        return False

def password_age_is_valid(user):

    #make sure time since latest password change event is less than PASSWORD_AGE_LIMIT_MINUTES

    try:
        password_change_event = PasswordChangeEvent.objects.filter(
            user=user,
        ).latest('created_date')

        age_limit = timedelta(minutes=settings.PASSWORD_AGE_LIMIT_MINUTES)
        age = timezone.now() - password_change_event.created_date
        logger.info(f'password age limit is {age_limit}')
        logger.info(f'password age is {age}')
        return age < age_limit

    except PasswordChangeEvent.DoesNotExist:
        return False

def should_warn_about_password_age(user):

    # warn if time since latest password change event is more than PASSWORD_AGE_WARN_MINUTES
    try:
        password_change_event = PasswordChangeEvent.objects.filter(
            user=user,
        ).latest('created_date')

        age_warn = timedelta(minutes=settings.PASSWORD_AGE_WARN_MINUTES)
        age = timezone.now() - password_change_event.created_date
        logger.info(f'password age warn is {age_warn}')
        logger.info(f'password age is {age}')
        return age > age_warn

    except PasswordChangeEvent.DoesNotExist:
        return False

def is_researcher(user):
    try:
        researcher = user.researcher
        return True
    except Researcher.DoesNotExist:
        return False

def is_participant(user):
    try:
        participant = user.participant
        return True
    except Participant.DoesNotExist:
        return False
