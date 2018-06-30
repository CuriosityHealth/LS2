from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from cryptography.fernet import InvalidToken

from .rest_pagination import DatapointListViewPagination

from django.conf import settings

from rest_framework.permissions import IsAuthenticated

from .models import Study, Researcher

from .rest_auth import (
    ParticipantTokenAuthentication,
    ParticipantAccountGeneratorAuthentication
)
from .rest_permissions import ParticipantAccountGeneratorPermission
from .models import Datapoint, Participant, ParticipantAccountGenerator
from .serializers import DatapointSerializer, ResearcherAPIAuthSerializer, ResearcherAPITokenSerializer

from easyaudit.settings import REMOTE_ADDR_HEADER
from easyaudit.models import LoginEvent

from django.db import IntegrityError, transaction

from .researcher_api_auth import ResearcherAPIDataFetchAuthentication

from .datapoint_controller import get_datapoint_queryset

import logging

import jwt

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = ResearcherAPIAuthSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        logger.debug('checking serializer')
        serializer.is_valid(raise_exception=True)
        logger.debug('checked serializer')

        ## from here, we've got researcher and study
        researcher = serializer.validated_data['researcher']
        logger.debug(f'researcher {researcher}')

        study = serializer.validated_data['study']
        logger.debug(f'study {study}')

        expiration_time = timezone.now() + timedelta(minutes=10)

        payload = {
            'sub': str(researcher.uuid),
            'exp': int(expiration_time.timestamp()),
            'study_id': str(study.uuid)
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        return Response({'token': token})

class Profile(APIView):
    authentication_classes = (ResearcherAPIDataFetchAuthentication,)
    permission_classes = ()

    def get(self, request, *args, **kwargs):

        decoded_token = self.request.user
        # logger.debug(f'request {decoded_token}')

        try:
            study = Study.objects.get(uuid=decoded_token.get('study_id'))
        except Study.DoesNotExist:
            return Response({'message': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            researcher = Researcher.objects.get(uuid=decoded_token.get('sub'))
        except Researcher.DoesNotExist:
            return Response({'message': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        if not researcher.user.is_active:
            return Response({'message': 'not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({'username': researcher.user.username, 'study_name': study.name})

class VerifyAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = ResearcherAPITokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})

        serializer.is_valid(raise_exception=True)

        ## Serializer takes care of checking for expired token
        decoded_token = serializer.validated_data['decoded_token']
        return Response({'message': 'success'})

class RefreshAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = ResearcherAPITokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})

        serializer.is_valid(raise_exception=True)

        decoded_token = serializer.validated_data['decoded_token']

        try:
            researcher = Researcher.objects.get(uuid=decoded_token.get('sub'))
        except Researcher.DoesNotExist:
            return Response({'message': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        if not researcher.user.is_active:
            return Response({'message': 'not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        ## Serializer takes care of checking for expired token

        expiration_time = timezone.now() + timedelta(minutes=10)

        payload = {
            'sub': decoded_token.get('sub'),
            'exp': int(expiration_time.timestamp()),
            'study_id': decoded_token.get('study_id')
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        return Response({'token': token})

class DatapointListView(ListAPIView):
    authentication_classes = (ResearcherAPIDataFetchAuthentication,)
    permission_classes = ()
    serializer_class = DatapointSerializer
    pagination_class = DatapointListViewPagination

    def get_queryset(self):

        decoded_token = self.request.user
        logger.debug(f'request {decoded_token}')

        try:
            researcher = Researcher.objects.get(uuid=decoded_token.get('sub'))
        except Researcher.DoesNotExist:
            return Response({'message': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        if not researcher.user.is_active:
            return Response({'message': 'not authorized'}, status=status.HTTP_401_UNAUTHORIZED)

        return get_datapoint_queryset(decoded_token.get('study_id'), self.request.query_params)
