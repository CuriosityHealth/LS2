from . import settings

def application_version_processor(requests):
    return {
        'application_version': settings.APPLICATION_VERSION,
    }