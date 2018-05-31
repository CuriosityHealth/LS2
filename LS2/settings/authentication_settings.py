import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
from django.conf import settings

def get_authentication_backends(environ):

    #default is false
    ldap_enabled = environ.get('LS2_LDAP_ENABLED', 'false').lower() == 'true'
    if ldap_enabled:
        return [
            'django_auth_ldap.backend.LDAPBackend',
            'study_management.auth_backends.RateLimitedAuthenticationBackend',
        ]
    else:
        return [
            'study_management.auth_backends.RateLimitedAuthenticationBackend',
        ]
        
def get_additional_settings(environ):

    additional_settings = {}

    ldap_enabled = environ.get('LS2_LDAP_ENABLED', 'false').lower() == 'true'
    if ldap_enabled:
        additional_settings["AUTH_LDAP_SERVER_URI"] = environ.get('LS2_LDAP_SERVER_URI')
        additional_settings["AUTH_LDAP_BIND_DN"] = environ.get('LS2_LDAP_BIND_DN')
        additional_settings["AUTH_LDAP_BIND_PASSWORD"] = environ.get('LS2_LDAP_BIND_PASSWORD')

        ldap_search_base_dn = environ.get('LS2_LDAP_SEARCH_BASE_DN')
        ldap_search_scope = ldap.SCOPE_SUBTREE
        ldap_search_filter = environ.get('LS2_LDAP_SEARCH_FILTER')
        additional_settings["AUTH_LDAP_USER_SEARCH"] = LDAPSearch(ldap_search_base_dn, ldap_search_scope, ldap_search_filter)
        additional_settings["AUTH_LDAP_ALWAYS_UPDATE_USER"] = True

    return additional_settings
