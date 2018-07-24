import urllib.request
import json


def get_database_settings(environ):

    database_settings = {}

    database_settings["DATABASES"] = environ.get("databases")
    database_settings["DATABASE_ROUTERS"] = environ.get('database_routers', [])
    fernet_keys = environ.get('fernet_keys')
    if len(fernet_keys) == 0 or len(fernet_keys[0]) == 0 or len(fernet_keys[0]) == 1:
        raise ImproperlyConfigured("Fernet keys improperly configured")

    database_settings["FERNET_KEYS"] = environ.get('fernet_keys')

    return database_settings

# def get_databases(environ):

#     # try:
#     #     databases_json_string = environ.get('DATABASE_JSON_STRING', '')
#     #     databases = json.loads(databases_json_string)
#     #     return environ.get('DATABASE_DICT')
#     # except ValueError:
#     #     return None

#     return environ.get('DATABASE_DICT')

# def get_database_routers(environ):

#     database_routers_string = environ.get('DATABASE_ROUTERS')
#     if database_routers_string == None:
#         return []
#     else:
#         return database_routers_string.split(',')

# def get_fernet_keys(environ):

#     fernet_keys_string = environ.get('FERNET_KEYS')
#     fernet_keys = fernet_keys_string.split('\n')
#     fernet_keys.reverse()
    # if len(fernet_keys) == 0 or len(fernet_keys[0]) == 0:
    #     raise ImproperlyConfigured("No FERNET_KEYS specified")

#     return fernet_keys
