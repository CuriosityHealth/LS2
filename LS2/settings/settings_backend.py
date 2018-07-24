from django.core.exceptions import ImproperlyConfigured
import json

def get_settings_environ(environ):

    # load settings config.json file
    settings_config_path = environ.get('LS2_SETTINGS_CONFIG_FILE', '/etc/ls2/settings/config.json')
    settings_config = json.load(open(settings_config_path, 'r'))

    if settings_config.get("LS2_SETTINGS_BACKEND") == 'local':
        return get_settings_from_environ(environ, settings_config)
    elif settings_config.get("LS2_SETTINGS_BACKEND") == 'aws-secretsmanager':
        return get_settings_from_aws_settings_manager(environ, settings_config)
    else:
        raise ImproperlyConfigured("Invalid settings backend")

def get_settings_from_environ(environ, settings_config):

    new_environ = {}

    settings_files = settings_config.get("LS2_SETTINGS_FILES")
    for filename in settings_files:
        settings_dict = json.load(open(filename, 'r'))
        new_environ.update(settings_dict)

    return new_environ

def get_settings_from_aws_settings_manager(environ, settings_config):
    ##AWS_ACCESS_KEY_ID
    aws_access_key_id = settings_config.get('AWS_ACCESS_KEY_ID')
    ##AWS_SECRET_ACCESS_KEY
    aws_secret_access_key = settings_config.get('AWS_SECRET_ACCESS_KEY')

    new_environ = {}

    secret_names = settings_config.get("SECRET_NAMES")
    for secret_name in secret_names:
        settings_dict = get_secret(aws_access_key_id, aws_secret_access_key, secret_name)
        new_environ.update(settings_dict)

    return new_environ

# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample code, visit the AWS docs:   
# https://aws.amazon.com/developers/getting-started/python/

import boto3
from botocore.exceptions import ClientError
# import json

def get_secret(aws_access_key_id, aws_secret_access_key, secret_name):
    endpoint_url = "https://secretsmanager.us-east-1.amazonaws.com"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:

        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise ImproperlyConfigured("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise ImproperlyConfigured("The request was invalid due to:", e)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise ImproperlyConfigured("The request had invalid params:", e)
    else:
        # Decrypted secret using the associated KMS CMK
        # Depending on whether the secret was a string or binary, one of these fields will be populated
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            binary_secret_data = get_secret_value_response['SecretBinary']
            
        # Your code goes here. 
        secret_json = json.loads(secret)
        return secret_json
        