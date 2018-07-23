import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
from django.conf import settings


def get_auth_settings(environ):

    auth_settings = {}
    auth_settings["AUTHENTICATION_BACKENDS"] = get_authentication_backends(environ)

    ldap_enabled = environ.get('LS2_LDAP_ENABLED', 'false').lower() == 'true'
    if ldap_enabled:
        auth_settings["AUTH_LDAP_SERVER_URI"] = environ.get('LS2_LDAP_SERVER_URI')
        auth_settings["AUTH_LDAP_BIND_DN"] = environ.get('LS2_LDAP_BIND_DN')
        auth_settings["AUTH_LDAP_BIND_PASSWORD"] = environ.get('LS2_LDAP_BIND_PASSWORD')

        ##disable cert checking
        auth_settings["AUTH_LDAP_GLOBAL_OPTIONS"] = {
            ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
            ldap.OPT_REFERRALS: ldap.OPT_OFF
        }

        ldap_search_base_dn = environ.get('LS2_LDAP_SEARCH_BASE_DN')
        ldap_search_scope = ldap.SCOPE_SUBTREE
        ldap_search_filter = environ.get('LS2_LDAP_SEARCH_FILTER')
        auth_settings["AUTH_LDAP_USER_SEARCH"] = LDAPSearch(ldap_search_base_dn, ldap_search_scope, ldap_search_filter)
        auth_settings["AUTH_LDAP_ALWAYS_UPDATE_USER"] = True

        ##blacklist the Participant API auth route
        ##This prevents participant auth from hitting LDAP server
        auth_settings["LS2_LDAP_AUTH_PATH_BLACKLIST"] = ['/dsu/auth/token']

    return auth_settings

def get_authentication_backends(environ):

    auth_backends = []

    model_auth_enabled = environ.get('LS2_MODEL_AUTH_ENABLED', 'true').lower() == 'true'
    if model_auth_enabled:
        auth_backends.append('study_management.auth_backends.RateLimitedAuthenticationBackend')

    #default is false
    ldap_enabled = environ.get('LS2_LDAP_ENABLED', 'false').lower() == 'true'
    if ldap_enabled:
        auth_backends.append('study_management.auth_backends.ProtectedLDAPAuthenticationBackend')

    if len(auth_backends) == 0:
        raise ImproperlyConfigured("Authentication backends improperly configured")

    return auth_backends
