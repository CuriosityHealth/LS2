from rest_framework import parsers, renderers
# from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from cryptography.fernet import InvalidToken
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated

from .rest_auth import (
    ParticipantTokenAuthentication,
    ParticipantAccountGeneratorAuthentication,
    TokenBasedParticipantAccountGeneratorAuthentication
)
from .rest_permissions import ParticipantAccountGeneratorPermission, TokenBasedParticipantAccountGeneratorPermission
from .models import Datapoint, Participant, ParticipantAccountGenerator, ParticipantAuthToken
from .serializers import DatapointSerializer

from easyaudit.settings import REMOTE_ADDR_HEADER
from easyaudit.models import LoginEvent

from django.db import IntegrityError, transaction

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=False)
        if 'user' in serializer.validated_data:
            user = serializer.validated_data['user']
            if user is not None:
                try:
                    participant = user.participant
                    token = ParticipantAuthToken.objects.create(user=user)

                    try:
                        with transaction.atomic():
                            login_event = LoginEvent.objects.create(login_type=LoginEvent.LOGIN,
                                                     username=user.username,
                                                     user=user,
                                                     remote_ip=request.META[REMOTE_ADDR_HEADER])
                    except:
                        pass

                    return Response({'token': token.key})
                except Participant.DoesNotExist:

                    #User authenticated but is not a participant
                    # print('user authenticated but is not a participant')
                    logger.info(f'user {user} authenticated but is not a participant')
                    try:
                        with transaction.atomic():
                            login_event = LoginEvent.objects.create(login_type=LoginEvent.FAILED,
                                                                    username=user.username,
                                                                    user=user,
                                                                    remote_ip=request.META[REMOTE_ADDR_HEADER])
                    except:
                        pass

                    content = {}
                    return Response(content, status=status.HTTP_401_UNAUTHORIZED)

            else:
                try:
                    with transaction.atomic():
                        login_event = LoginEvent.objects.create(login_type=LoginEvent.FAILED,
                                                                username=user.username,
                                                                user=user,
                                                                remote_ip=request.META[REMOTE_ADDR_HEADER])
                except:
                    pass

                content = {}
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # Only need to do below in the case that username is not specified in serializer
            # Otherwise, this will have been handled by the default login failed signal
            if not serializer.data.get('username'):
                try:
                    with transaction.atomic():
                        login_event = LoginEvent.objects.create(login_type=LoginEvent.FAILED,
                                                                username="Username field not speficied",
                                                                remote_ip=request.META[REMOTE_ADDR_HEADER])
                except Exception as e:
                    # print(e)
                    pass

            content = {}
            return Response(content, status=status.HTTP_401_UNAUTHORIZED)

class ParticipantLogOutView(APIView):

    authentication_classes = (ParticipantTokenAuthentication,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        user = request.user
        token = request.auth
        try:
            with transaction.atomic():
                login_event = LoginEvent.objects.create(login_type=LoginEvent.LOGOUT,
                                                        username=getattr(user, user.USERNAME_FIELD),
                                                        user=user,
                                                        remote_ip=request.META[REMOTE_ADDR_HEADER])

            token.delete()
        except:
            pass

        return Response({"message":"success"}, status.HTTP_200_OK)

class ParticipantTokenCheck(APIView):

    authentication_classes = (ParticipantTokenAuthentication,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        return Response({"message":"success"}, status.HTTP_200_OK)

class DatapointCreateView(APIView):

    authentication_classes = (ParticipantTokenAuthentication,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        try:
            participant = request.user.participant
        except Participant.DoesNotExist:
            content = {}
            return Response(content, status=status.HTTP_401_UNAUTHORIZED)

        logger.debug(f'datapoint is {request.data}')
        serializer = DatapointSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                uuid = serializer.validated_data['uuid']
                message = f'A datapoint with id {uuid} already exists.'
                return Response({"message": message}, status=status.HTTP_409_CONFLICT)
        else:
            logger.debug(f'datapoint is invalid {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


##This authenticates users as AnonymousUser, but puts the generator in the auth field
class ParticipantAccountGeneratorView(APIView):

    authentication_classes = (ParticipantAccountGeneratorAuthentication,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (ParticipantAccountGeneratorPermission,)

    def post(self, request, format=None):

        participant_account_generator = request.auth
        username_password = participant_account_generator.generate_participant()
        if username_password == None:
            return Response({"error": "An error occurred. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {'username': username_password[0], 'password': username_password[1]}
        return Response(content, status=status.HTTP_201_CREATED)

#This authenticates a token, then generates an account
class TokenBasedParticipantAccountGeneratorView(APIView):

    authentication_classes = (TokenBasedParticipantAccountGeneratorAuthentication,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (TokenBasedParticipantAccountGeneratorPermission,)

    def post(self, request, format=None):

        participant_account_token = request.user
        participant_account_generator = participant_account_token.account_generator

        if participant_account_generator.can_redeem_token() == False:
            return Response({"error": "The token generator is disabled. Please contact the administrator."}, status=status.HTTP_403_FORBIDDEN)


        hasBeenUsed = None
        with transaction.atomic():
            participant_account_token.refresh_from_db()
            hasBeenUsed = participant_account_token.used
            if hasBeenUsed == False:
                participant_account_token.used = True
                participant_account_token.used_date_time = timezone.now()
                participant_account_token.save()

        if hasBeenUsed:
            return Response({"error": "The token is invalid. Please try again with a new token."}, status=status.HTTP_400_BAD_REQUEST)

        ##generate participant from token
        username_password = participant_account_generator.generate_participant(participant_account_token)

        if username_password == None:
            return Response({"error": "An error occurred. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        content = {'username': username_password[0], 'password': username_password[1]}
        return Response(content, status=status.HTTP_201_CREATED)
