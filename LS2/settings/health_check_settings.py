from django.conf import settings

def get_settings(environ):
    additional_settings = {}

    additional_settings["LS2_BACKUP_AGE_MINS_MAX"] = int(environ.get('LS2_BACKUP_AGE_MINS_MAX', 48*60))
    additional_settings["LS2_BACKUP_HEALTH_CHECK_ENABLED"] = environ.get('LS2_BACKUP_HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    
    return additional_settings
