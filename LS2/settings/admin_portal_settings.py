from django.conf import settings

def get_additional_settings(environ):
    additional_settings = {}

    additional_settings["ADMIN_PORTAL_ROOT"] = environ.get('LS2_ADMIN_PORTAL_ROOT', 'admin/')
    additional_settings["LOGIN_REDIRECT_URL"] ='/admin/'
    additional_settings["LOGIN_URL"] = '/admin/login/'
    additional_settings["LOGOUT_REDIRECT_URL"] = '/admin/'
    
    return additional_settings
