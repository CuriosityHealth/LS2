from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication, BaseAuthentication
)

from django.contrib.auth.models import AnonymousUser
from .utils import is_researcher, is_participant
from .models import (
    ParticipantAccountGenerator,
    ParticipantAccountGenerationRequestEvent,
    ParticipantAccountGenerationTimeout
)
from .serializers import ParticipantAccountGeneratorAuthenticationSerializer

from django.db import IntegrityError, transaction
from easyaudit.settings import REMOTE_ADDR_HEADER

from datetime import datetime, timedelta
from django.utils import timezone
from . import settings

from .utils import get_client_ip

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ResearcherSessionAuthentication(SessionAuthentication):

    def authenticate(self, request):

        user_tuple = super().authenticate(request)
        if user_tuple != None and is_researcher(user_tuple[0]):
            return user_tuple
        else:
            return None

class ParticipantTokenAuthentication(TokenAuthentication):

    def authenticate(self, request):

        user_tuple = super().authenticate(request)
        if user_tuple != None and is_participant(user_tuple[0]):
            return user_tuple

        else:
            return None

class ParticipantAccountGeneratorAuthentication(BaseAuthentication):

    def disabled_via_timeout(self, generator_id, remote_ip):
        try:

            generation_timeout = ParticipantAccountGenerationTimeout.objects.filter(
                generator_id=generator_id,
                remote_ip=remote_ip,
                disable_until__gt=timezone.now()
            ).latest('disable_until')

            if generation_timeout != None and generation_timeout.disabled():
                logger.debug("Generation is disabled")
                return True
            else:
                return False

        except ParticipantAccountGenerationTimeout.DoesNotExist:
            return False

    def should_throttle(self, generator_id, remote_ip):

        if settings.PARTICIPANT_ACCOUNT_GENERATOR_LOGIN_RATE_LIMIT_ENABLED == False:
            return False

        ## check for existing timeout
        if self.disabled_via_timeout(generator_id, remote_ip):
            return True

        now = timezone.now()
        since_time = timedelta(minutes=settings.PARTICIPANT_ACCOUNT_GENERATOR_RATE_LIMIT_WINDOW_MINUTES)
        earlier = now - since_time

        logger.info(f'minutes {settings.PARTICIPANT_ACCOUNT_GENERATOR_RATE_LIMIT_WINDOW_MINUTES}')

        try:
            generation_requests = ParticipantAccountGenerationRequestEvent.objects.filter(
                remote_ip=remote_ip,
                generator_id=generator_id,
                created_date__gt=earlier
            )
        except ParticipantAccountGenerationRequestEvent.DoesNotExist:
            return False

        logger.info(f'there have been {generation_requests.count()} generation requests')

        if generation_requests.count() >= settings.PARTICIPANT_ACCOUNT_GENERATOR_RATE_LIMIT_REQUESTS:
            ## we should create a timeout here
            disable_until = now + timedelta(minutes=settings.PARTICIPANT_ACCOUNT_GENERATOR_RATE_LIMIT_TIMEOUT_MINUTES)
            generation_timeout = \
                ParticipantAccountGenerationTimeout.objects.create(
                    generator_id=generator_id,
                    remote_ip=remote_ip,
                    disable_until=disable_until
                )

            logger.debug(generation_timeout)

            return True



    def authenticate(self, request):

        # now = timezone.now()
        # since_time = timedelta(minutes=settings.LOGIN_RATE_LIMIT_WINDOW_MINUTES)
        # earlier = now - since_time
        #
        # try:
        #     failed_login_attempts = LoginEvent.objects.filter(
        #         username=instance.username,
        #         remote_ip=instance.remote_ip,
        #         login_type=LoginEvent.FAILED,
        #         datetime__gt=earlier,
        #     )
        #
        # except LoginEvent.DoesNotExist:
        #     return
        #
        # logger.info(f'there have been {failed_login_attempts.count()} failed login attempts')
        # if failed_login_attempts.count() >= settings.LOGIN_RATE_LIMIT_FAILED_ATTEMPTS and \
        #     should_disable_login(instance.username, instance.remote_ip) == False:
        #
        #     logger.info('we should throttle here!!!')
        #     diable_until = now + timedelta(minutes=settings.LOGIN_RATE_LIMIT_TIMEOUT_MINUTES)
        #     login_timeout = LoginTimeout.objects.create(
        #         disable_until=diable_until,
        #         username=instance.username,
        #         remote_ip=instance.remote_ip
        #     )

        remote_ip = get_client_ip(request)
        ## Log Event Here
        serializer = ParticipantAccountGeneratorAuthenticationSerializer(data=request.data)
        if not serializer.is_valid():
            try:
                with transaction.atomic():
                    generation_request_event = \
                        ParticipantAccountGenerationRequestEvent.objects.create(
                            generator_id=None,
                            remote_ip=remote_ip
                        )
            except:
                pass

            return None

        logger.debug(serializer.validated_data)

        generator_id = serializer.validated_data['generator_id']
        generator_password = serializer.validated_data['generator_password']

        try:
            with transaction.atomic():
                logger.debug("GENERATING RequestEvent")
                generation_request_event = ParticipantAccountGenerationRequestEvent.objects.create(
                        generator_id=generator_id,
                        remote_ip=remote_ip
                    )

                logger.debug(generation_request_event)
        except:
            pass

        if generator_id == None or generator_password == None:
            return None

        if self.should_throttle(generator_id, remote_ip):
            return None

        try:
            generator = ParticipantAccountGenerator.objects.get(uuid=generator_id)
            logger.debug(generator)
            if generator.check_password(generator_password):
                return (AnonymousUser(), generator)

        except ParticipantAccountGenerator.DoesNotExist:
            return None

        return None
