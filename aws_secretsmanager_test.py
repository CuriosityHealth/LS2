# this can be run using the following command while the container is not running
# docker-compose run --rm study_management_portal python aws_secretsmanager_test.py

import os
import json

from LS2.settings.settings_backend import load_settings_from_aws_secrets_manager

def main():
    settings_config_path = os.environ.get('LS2_SETTINGS_CONFIG_FILE', '/etc/ls2/settings/config.json')
    settings_config = json.load(open(settings_config_path, 'r'))

    # print("settings config")
    # print(settings_config)
    if settings_config.get("LS2_SETTINGS_BACKEND") == 'aws-secretsmanager':
        settings = load_settings_from_aws_secrets_manager(settings_config)
        # print(settings)
        if 'common' in settings and 'app' in settings:
            print("Configuration may be valid")
        else:
            raise ImproperlyConfigured("An error occurred fetching settings")
    else:
        raise ImproperlyConfigured("Invalid settings backend")
  
if __name__ == "__main__":
    main()