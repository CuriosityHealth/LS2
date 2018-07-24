from django.conf import settings

def get_additional_settings(environ):
    additional_settings = {}
    
    ## Data Export
    additional_settings["DATA_EXPORT_ENABLED"] = environ.get('LS2_DATA_EXPORT_ENABLED', True)
    additional_settings["DATA_DOWNLOAD_DEFAULT"] = environ.get('LS2_DATA_DOWNLOAD_DEFAULT', False)

    additional_settings["LOGIN_REDIRECT_URL"] = 'researcher_home'
    additional_settings["LOGIN_URL"] = 'researcher_login'
    additional_settings["LOGOUT_REDIRECT_URL"] = 'researcher_login'

    return additional_settings
