import os
import sys
import ldap
import getpass
from django_auth_ldap.config import LDAPSearch
from LS2.settings import settings_backend

def main():

    os_environ_dict = dict(os.environ)
    environ = settings_backend.get_settings_environ(os_environ_dict)

    ldap_enabled = environ.get('LS2_LDAP_ENABLED', False)
    if ldap_enabled == False:
        sys.exit("LDAP is not enabled")

    server_uri = environ.get('LS2_LDAP_SERVER_URI')
    print(f'Attempting to connect to {server_uri}')

    ##ignore cert errors for now
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

    ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)

    l = ldap.initialize(server_uri, trace_level=0)
    print(l)
    print(f'Server initialization success')

    bind_dn = environ.get('LS2_LDAP_BIND_DN')
    bind_password = environ.get('LS2_LDAP_BIND_PASSWORD')
    if bind_dn == None or bind_password == None:
        sys.exit("LDAP bind user info missing")

    print(f'Attempting to bind with DN {bind_dn}')
    r = l.simple_bind_s(bind_dn, bind_password)

    print(f'Bind Successful')
    ldap_search_base_dn = environ.get('LS2_LDAP_SEARCH_BASE_DN')
    ldap_search_scope = ldap.SCOPE_SUBTREE
    ldap_search_filter_template = environ.get('LS2_LDAP_SEARCH_FILTER')

    user = input("Enter a username: ")
    password = getpass.getpass()

    print(f'Attempting to search for {user} in \"{ldap_search_base_dn}\"')

    # filter = ldap_search_filter_template % {'user': user}
    print(f'Filter {filter}')
    # result = l.search_s(ldap_search_base_dn,ldap_search_scope,filter)[0]
    # print(result[0])
    # user_dn = result[0]

    # r = l.simple_bind_s(user_dn, password)
    # print('Test Successful')

    ldap_search = LDAPSearch(ldap_search_base_dn, ldap.SCOPE_SUBTREE, ldap_search_filter_template)

    print(ldap_search)
    results = ldap_search.execute(l, {'user': user})
    if results is not None and len(results) == 1:
        # print(results[0])
        pass
    else:
        print("NOT FOUND")

    user_dn = results[0][0]
    l.simple_bind_s(user_dn, password)
    print('Test Successful')


if __name__ == "__main__":
    main()
