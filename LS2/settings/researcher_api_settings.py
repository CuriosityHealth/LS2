from django.conf import settings

def get_additional_settings(environ):
    additional_settings = {}

    additional_settings["RESEARCHER_API_TOKEN_LIFETIME_MINS"] = environ.get('LS2_RESEARCHER_API_TOKEN_LIFETIME_MINS', 10)

    return additional_settings
