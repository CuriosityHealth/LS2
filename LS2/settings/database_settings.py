import urllib.request
import json


def get_database_settings(environ):

    database_settings = {}

    databases = get_databases(environ)
    if databases == None:
        raise ImproperlyConfigured("Databases improperly configured")
    else:
        database_settings["DATABASES"] = databases

    database_settings["DATABASE_ROUTERS"] = get_database_routers(environ)
    database_settings["FERNET_KEYS"] = get_fernet_keys(environ)

    return database_settings

def get_databases(environ):

    try:
        databases_json_string = environ.get('DATABASE_JSON_STRING', '')
        databases = json.loads(databases_json_string)
        return databases
    except ValueError:
        return None

def get_database_routers(environ):

    database_routers_string = environ.get('DATABASE_ROUTERS')
    if database_routers_string == None:
        return []
    else:
        return database_routers_string.split(',')

def get_fernet_keys(environ):

    fernet_keys_string = environ.get('FERNET_KEYS')
    fernet_keys = fernet_keys_string.split('\n')
    fernet_keys.reverse()
    if len(fernet_keys) == 0 or len(fernet_keys[0]) == 0:
        raise ImproperlyConfigured("No FERNET_KEYS specified")

    return fernet_keys
