from rest_framework import permissions
from .models import ParticipantAccountGenerator, ParticipantAccountToken

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

## might also want to add a check for IPs
class ParticipantAccountGeneratorPermission(permissions.BasePermission):


    def has_permission(self, request, view):

        if type(request.auth) != ParticipantAccountGenerator:
            return False

        generator = request.auth
        logger.debug('checking permissions')
        logger.debug(generator)
        return generator.can_generate_participant_account()

class TokenBasedParticipantAccountGeneratorPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        logger.debug('checking permissions')
        logger.debug(request.user)

        return type(request.user) == ParticipantAccountToken
