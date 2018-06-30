from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from .models import Datapoint, Study
import json

from django.db import IntegrityError, transaction
from easyaudit.settings import REMOTE_ADDR_HEADER
from easyaudit.models import LoginEvent
from .utils import is_researcher

import jwt
from django.conf import settings

import logging

logger = logging.getLogger(__name__)

class DatapointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Datapoint
        # fields = ('id', 'participant', 'study', 'uuid')
        fields = '__all__'

    def to_internal_value(self, data):

        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError({
                'request': 'The request is required as part of the context.'
            })

        try:
            participant = request.user.participant
            participant_uuid = participant.uuid
            study_uuid = participant.study.uuid
        except Participant.DoesNotExist:
            raise serializers.ValidationError({
                'participant': 'The request must include a valid participant.'
            })

        header = data.get('header')

        # Perform the data validation.
        if not header:
            raise serializers.ValidationError({
                'header': 'This field is required.'
            })

        uuid = header.get('id')
        if not uuid:
            raise serializers.ValidationError({
                'header.id': 'This field is required.'
            })

        schema = header.get('schema_id')
        if not schema:
            raise serializers.ValidationError({
                'header.schema': 'This field is required.'
            })


        schema_namespace = schema.get('namespace')
        if not schema_namespace:
            raise serializers.ValidationError({
                'header.schema.namespace': 'This field is required.'
            })

        schema_name = schema.get('name')
        if not schema_name:
            raise serializers.ValidationError({
                'header.schema.name': 'This field is required.'
            })


        schema_version = schema.get('version')
        if not schema_version:
            raise serializers.ValidationError({
                'header.schema.version': 'This field is required.'
            })


        split_version = schema_version.split('.')
        if len(split_version) != 3:
            raise serializers.ValidationError({
                'header.schema.version': 'This field must support semantic versioning (i.e., major.minor.patch).'
            })

        try:
            schema_version_major = int(split_version[0])
            schema_version_minor = int(split_version[1])
            schema_version_patch = int(split_version[2])
        except ValueError:
            raise serializers.ValidationError({
                'header.schema.version': 'This field must support semantic versioning (i.e., major.minor.patch).'
            })
        except Exception:
            raise serializers.ValidationError({
                'header.schema.version': 'This field must support semantic versioning (i.e., major.minor.patch).'
            })

        acquisition_provenance = header.get('acquisition_provenance')
        if not acquisition_provenance:
            raise serializers.ValidationError({
                'header.acquisition_provenance': 'This field is required.'
            })

        ap_source_name = acquisition_provenance.get('source_name')
        if not ap_source_name:
            raise serializers.ValidationError({
                'header.acquisition_provenance.source_name': 'This field is required.'
            })

        ap_source_creation_date_time = acquisition_provenance.get('source_creation_date_time')
        if not ap_source_creation_date_time:
            raise serializers.ValidationError({
                'header.acquisition_provenance.source_creation_date_time': 'This field is required.'
            })

        ap_source_modality = acquisition_provenance.get('modality')
        if not ap_source_modality:
            raise serializers.ValidationError({
                'header.acquisition_provenance.modality': 'This field is required.'
            })

        body = json.dumps(data.get('body'))

        if not body:
            raise serializers.ValidationError({
                'body': 'This field is required.'
            })

        internal_representation = {
            'participant_uuid': participant_uuid,
            'study_uuid': study_uuid,
            'uuid': uuid,
            'schema_namespace': schema_namespace,
            'schema_name': schema_name,
            'schema_version_major': schema_version_major,
            'schema_version_minor': schema_version_minor,
            'schema_version_patch': schema_version_patch,
            'ap_source_name': ap_source_name,
            'ap_source_creation_date_time': ap_source_creation_date_time,
            'ap_source_modality': ap_source_modality,
            'body': body
        }

        headerJSON = header.get('metadata')
        if headerJSON != None:
            internal_representation['metadata'] = json.dumps(headerJSON)

        return internal_representation

    def to_representation(self, obj):

        schema_version = '.'.join([
            str(obj.schema_version_major),
            str(obj.schema_version_minor),
            str(obj.schema_version_patch),
        ])

        header = {
            'participant_id': obj.participant_uuid,
            'id': obj.uuid,
            'creation_date_time': obj.created_date_time,
            'schema_id': {
                'namespace': obj.schema_namespace,
                'name': obj.schema_name,
                'version': schema_version,
            },
            'acquisition_provenance': {
                'source_name': obj.ap_source_name,
                'modality': obj.ap_source_modality,
                'source_creation_date_time': obj.ap_source_creation_date_time,
            }
        }

        if obj.metadata != None:
            header['metadata'] = json.loads(obj.metadata)

        return {
            'header': header,
            'body': json.loads(obj.body)
        }

class ParticipantAccountGeneratorAuthenticationSerializer(serializers.Serializer):
    generator_id = serializers.UUIDField()
    generator_password = serializers.CharField()

class ResearcherAPIAuthSerializer(AuthTokenSerializer):
    study_id = serializers.UUIDField()

    def validate(self, attrs):

        request = self.context.get('request')

        logger.debug('validating ResearcherAPIAuthSerializer')
        logger.debug(attrs)
        attrs = super().validate(attrs)
        logger.debug('returned attrs from AuthTokenSerializer')
        logger.debug(attrs)

        user = attrs['user']

        #check to see if user is a researcher
        if user != None and is_researcher(user):
            researcher = user.researcher
            attrs['researcher'] = researcher
        else:
            with transaction.atomic():
                login_event = LoginEvent.objects.create(login_type=LoginEvent.FAILED,
                                                        username=user.username,
                                                        user=user,
                                                        remote_ip=request.META[REMOTE_ADDR_HEADER])

            msg = 'User is not a researcher'
            raise serializers.ValidationError(msg, code='authorization')

        ## check to see if researcher has access to study
        study_id = attrs.get('study_id')

        if study_id:
            try:
                study = researcher.studies.get(uuid=study_id)
            except Study.DoesNotExist:

                with transaction.atomic():
                    login_event = LoginEvent.objects.create(login_type=LoginEvent.FAILED,
                                                            username=user.username,
                                                            user=user,
                                                            remote_ip=request.META[REMOTE_ADDR_HEADER])

                msg = 'researcher does not have access to study_id'
                raise serializers.ValidationError(msg, code='authorization')

        else:
            msg = 'must include study_id'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['study'] = study
        return attrs

class ResearcherAPITokenSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):

        token = attrs['token']

        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.exceptions.DecodeError:
            msg = 'invalid token'
            raise serializers.ValidationError(msg, code='authorization')
        except jwt.exceptions.ExpiredSignatureError:
            msg = 'token expired'
            raise serializers.ValidationError(msg, code='authorization')
        attrs['decoded_token'] = decoded_token
        return attrs
