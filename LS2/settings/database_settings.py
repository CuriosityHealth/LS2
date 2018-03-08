import urllib.request
import json


def get_databases(environ):

    file_url = environ.get('DATABASE_SETTINGS_URL', '')
    with urllib.request.urlopen(file_url) as database_file:
        databases = json.load(database_file)
        return databases

    return None
