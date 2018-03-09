import urllib.request
import json


def get_databases(environ):

    try:
        databases_json_string = environ.get('DATABASE_JSON_STRING', '')
        databases = json.loads(databases_json_string)
        return databases
    except ValueError:
        return None
