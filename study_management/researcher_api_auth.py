from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

import logging

import jwt

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ResearcherAPIDataFetchAuthentication(BaseAuthentication):

    def authenticate(self, request):

        logger.debug(f'authenticating')

        token = request.META.get('HTTP_AUTHORIZATION').replace('Token ', '')

        logger.debug(token)
        # logger.debug(request.META)
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.exceptions.DecodeError:
            raise AuthenticationFailed()
        except jwt.exceptions.ExpiredSignatureError:
            raise AuthenticationFailed()

        #lookup researcher
        
        return (decoded_token, None)
