from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication, BaseAuthentication
)

from django.contrib.auth.models import AnonymousUser
from .utils import is_researcher, is_participant
from .models import ParticipantAccountGenerator
from .serializers import ParticipantAccountGeneratorAuthenticationSerializer

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

    def authenticate(self, request):

        serializer = ParticipantAccountGeneratorAuthenticationSerializer(data=request.data)
        if not serializer.is_valid():
            return None

        logger.debug(serializer.validated_data)

        generator_id = serializer.validated_data['generator_id']
        generator_password = serializer.validated_data['generator_password']
        if generator_id == None or generator_password == None:
            return None

        try:
            generator = ParticipantAccountGenerator.objects.get(uuid=generator_id)
            logger.debug(generator)
            if generator.check_password(generator_password):
                return (AnonymousUser(), generator)

        except ParticipantAccountGenerator.DoesNotExist:
            return None

        return None
