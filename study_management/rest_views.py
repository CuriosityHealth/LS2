from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from cryptography.fernet import InvalidToken

# from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .decorators import researcher_login_required
from .rest_auth import ResearcherSessionAuthentication, ParticipantTokenAuthentication
from .models import Datapoint, Participant, Researcher, Study
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
            # print(user)
            if user is not None:
                try:
                    # print(user.participant)
                    participant = user.participant
                    Token.objects.filter(user=user).delete()
                    token = Token.objects.create(user=user)

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
            # print('user is not in serializer.validated_data')
            # print("user is nil")
            # Only need to do below in the case that username is not specified in serializer
            # Otherwise, this will have been handled by the default login failed signal
            # print(serializer.data)
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
        try:
            with transaction.atomic():
                login_event = LoginEvent.objects.create(login_type=LoginEvent.LOGOUT,
                                                        username=getattr(user, user.USERNAME_FIELD),
                                                        user=user,
                                                        remote_ip=request.META[REMOTE_ADDR_HEADER])

            Token.objects.filter(user=user).delete()
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

class DatapointListView(APIView):
    authentication_classes = (ResearcherSessionAuthentication,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, study_uuid, participant_uuid=None, format=None):

        ##This ensures that the user is a researcher
        ## This should not happen, but let's leave here for safety
        try:
            researcher = request.user.researcher
        except Researcher.DoesNotExist:
            return render(request, '404.html')

        ##This ensures that researcher has access to this study
        try:
            study = researcher.studies.get(uuid=study_uuid)
        except Study.DoesNotExist:
            return render(request, '404.html')

        datapoints = Datapoint.objects.filter(study=study).order_by('created_date_time')
        if participant_uuid is not None:
            datapoints = datapoints.filter(participant__uuid=participant_uuid)
            
        try:
            serializer = DatapointSerializer(datapoints, many=True)
            return Response(serializer.data)
        except InvalidToken:
            return render(request, '500.html')

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

        serializer = DatapointSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                uuid = serializer.validated_data['uuid']
                message = f'A datapoint with id {uuid} already exists.'
                return Response({"message": message}, status=status.HTTP_409_CONFLICT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
