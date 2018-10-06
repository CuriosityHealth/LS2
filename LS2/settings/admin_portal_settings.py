from django.conf import settings

def get_additional_settings(environ):
    additional_settings = {}

    admin_portal_root = environ.get('LS2_ADMIN_PORTAL_ROOT', 'admin/')
    additional_settings["ADMIN_PORTAL_ROOT"] = admin_portal_root

    additional_settings["LOGIN_REDIRECT_URL"] = "/" + admin_portal_root
    additional_settings["LOGIN_URL"] =  "/" + admin_portal_root + "login/"
    additional_settings["LOGOUT_REDIRECT_URL"] =  "/" + admin_portal_root

    additional_settings["AUDIT_LOG_RETENTION_DAYS"] = environ.get('AUDIT_LOG_RETENTION_DAYS', 90)
    
    return additional_settings
