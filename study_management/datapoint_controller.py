from .models import Datapoint
import uuid
import logging
from rest_framework import exceptions

# Get an instance of a logger
logger = logging.getLogger(__name__)

def get_datapoint_queryset(study_uuid, parameters):

    queryset = Datapoint.objects.filter(study_uuid=study_uuid)

    ## we could also whitelist certain namespaces / names for each client
    ## the idea here is that if we would like to restrict certain clients to certain data types
    ## e.g., CH only gets access to the usage metrics

    ##Additional filters
    ## - Since, Before Date
    ##

    schema_name = parameters.get('schema_name', None)
    if schema_name is not None:
        queryset = queryset.filter(schema_name=schema_name)

    schema_namespace = parameters.get('schema_namespace', None)
    if schema_namespace is not None:
        queryset = queryset.filter(schema_namespace=schema_namespace)

    version_min = parameters.get('version_min', None)
    if version_min is not None:
        sem_ver_min = semantic_version.Version(version_min, partial=True)
        logger.debug(f'sem_ver_min {sem_ver_min}: {list(sem_ver_min)}')
        if sem_ver_min.major is not None:
            queryset = queryset.filter(schema_version_major__gte=sem_ver_min.major)
        if sem_ver_min.minor is not None:
            queryset = queryset.filter(schema_version_minor__gte=sem_ver_min.minor)
        if sem_ver_min.patch is not None:
            queryset = queryset.filter(schema_version_patch__gte=sem_ver_min.patch)

    version_max = parameters.get('version_max', None)
    if version_max is not None:
        sem_ver_max = semantic_version.Version(version_max, partial=True)
        logger.debug(f'sem_ver_max {sem_ver_max}: {list(sem_ver_max)}')
        if sem_ver_max.major is not None:
            queryset = queryset.filter(schema_version_major__lt=sem_ver_max.major)
        if sem_ver_max.minor is not None:
            queryset = queryset.filter(schema_version_minor__lt=sem_ver_max.minor)
        if sem_ver_max.patch is not None:
            queryset = queryset.filter(schema_version_patch__lt=sem_ver_max.patch)

    participant_id = parameters.get('participant_id', None)
    if participant_id is not None:
        try:
            participant_uuid = uuid.UUID(participant_id)
            queryset = queryset.filter(participant_uuid=participant_uuid)
        except ValueError as e:
            raise exceptions.ParseError()
        except:
            raise exceptions.NotFound()

    ordering = parameters.get('ordering', None)
    if ordering == 'desc':
        queryset = queryset.order_by('-created_date_time')
    else:
        queryset = queryset.order_by('created_date_time')

    logger.debug(queryset.query)

    return queryset
