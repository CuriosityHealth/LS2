from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
from LS2.settings import settings_backend
import ldap
import getpass
from django_auth_ldap.config import LDAPSearch

class Command(BaseCommand):
    help = 'Tests the LDAP connection'

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):

        os_environ_dict = dict(os.environ)
        environ = settings_backend.get_settings_environ(os_environ_dict)

        ldap_enabled = environ.get('LS2_LDAP_ENABLED', False)
        if ldap_enabled == False:
            raise CommandError("LDAP is not enabled")

        server_uri = environ.get('LS2_LDAP_SERVER_URI')
        if server_uri == None:
            raise CommandError("LDAP server URI info missing")

        self.stdout.write(self.style.SUCCESS(f'Attempting to connect to {server_uri}'))

        ##ignore cert errors for now
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)

        l = ldap.initialize(server_uri, trace_level=0)
        self.stdout.write(self.style.SUCCESS(f'Server initialization success'))

        bind_dn = environ.get('LS2_LDAP_BIND_DN')
        bind_password = environ.get('LS2_LDAP_BIND_PASSWORD')
        if bind_dn == None or bind_password == None:
            raise CommandError("LDAP bind user info missing")

        self.stdout.write(self.style.SUCCESS(f'Attempting to bind with DN {bind_dn}'))
        r = l.simple_bind_s(bind_dn, bind_password)
        self.stdout.write(self.style.SUCCESS(f'Bind Successful'))

        ldap_search_base_dn = environ.get('LS2_LDAP_SEARCH_BASE_DN')
        ldap_search_scope = ldap.SCOPE_SUBTREE
        ldap_search_filter_template = environ.get('LS2_LDAP_SEARCH_FILTER')

        user = options['username']
        password = getpass.getpass()

        self.stdout.write(f'Attempting to search for {user} in \"{ldap_search_base_dn}\"')
        self.stdout.write(f'Filter {filter}')

        ldap_search = LDAPSearch(ldap_search_base_dn, ldap.SCOPE_SUBTREE, ldap_search_filter_template)

        results = ldap_search.execute(l, {'user': user})
        if results is not None and len(results) == 1:
            pass
        else:
            raise CommandError("NOT FOUND")

        user_dn = results[0][0]
        l.simple_bind_s(user_dn, password)
        self.stdout.write('Test Successful')