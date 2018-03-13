import urllib.request
import json


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
