from rest_framework import parsers, renderers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from cryptography.fernet import InvalidToken

from rest_framework.permissions import IsAuthenticated

from .rest_auth import (
    ResearcherSessionAuthentication
)

from .models import Datapoint, Researcher, Study, Participant
from .serializers import DatapointSerializer, ParticipantMappingSerializer

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

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
        ##TODO: Can we take this check out? OR move to permissions check?
        try:
            study = researcher.studies.get(uuid=study_uuid)
        except Study.DoesNotExist:
            return render(request, '404.html')

        datapoints = Datapoint.objects.filter(study_uuid=study_uuid).order_by('created_date_time')
        if participant_uuid is not None:
            datapoints = datapoints.filter(participant_uuid=participant_uuid)

        try:
            serializer = DatapointSerializer(datapoints, many=True)
            return Response(serializer.data)
        except InvalidToken:
            return render(request, '500.html')

class ParticipantMappingListView(APIView):
    authentication_classes = (ResearcherSessionAuthentication,)
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, study_uuid, format=None):

        ##This ensures that the user is a researcher
        ## This should not happen, but let's leave here for safety
        try:
            researcher = request.user.researcher
        except Researcher.DoesNotExist:
            return render(request, '404.html')

        ##This ensures that researcher has access to this study
        ##TODO: Can we take this check out? OR move to permissions check?
        try:
            study = researcher.studies.get(uuid=study_uuid)
        except Study.DoesNotExist:
            return render(request, '404.html')

        participants = Participant.objects.filter(study=study)

        try:
            serializer = ParticipantMappingSerializer(participants, many=True)
            return Response(serializer.data)
        except InvalidToken:
            return render(request, '500.html')
