from django.core.exceptions import ImproperlyConfigured
import json

def get_settings_environ(environ):

    # load settings config.json file
    settings_config_path = environ.get('LS2_SETTINGS_CONFIG_FILE', '/etc/ls2/settings/config.json')
    settings_config = json.load(open(settings_config_path, 'r'))

    settings = {}

    if settings_config.get("LS2_SETTINGS_BACKEND") == 'local':
        settings = load_settings_from_file(settings_config)

    elif settings_config.get("LS2_SETTINGS_BACKEND") == 'aws-secretsmanager':
        settings = load_settings_from_aws_secrets_manage(settings_config)

    else:
        raise ImproperlyConfigured("Invalid settings backend")

    new_environ = settings.get('common', {})
    app_config_id = environ.get('APP_CONFIG_ID')
    if app_config_id != None:
        app_config = settings.get('app', {}).get(app_config_id, {})
        new_environ.update(app_config)
        
    return new_environ


def load_settings_from_file(settings_config):
    settings_file = settings_config.get("LS2_SETTINGS_FILE")
    return json.load(open(settings_file, 'r'))

def load_settings_from_aws_secrets_manage(settings_config):
    ##AWS_ACCESS_KEY_ID
    aws_access_key_id = settings_config.get('AWS_ACCESS_KEY_ID')
    ##AWS_SECRET_ACCESS_KEY
    aws_secret_access_key = settings_config.get('AWS_SECRET_ACCESS_KEY')

    secret_name = settings_config.get("SECRET_NAME")

    return get_secret(aws_access_key_id, aws_secret_access_key, secret_name)

# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample code, visit the AWS docs:   
# https://aws.amazon.com/developers/getting-started/python/

import boto3
from botocore.exceptions import ClientError

def get_secret(aws_access_key_id, aws_secret_access_key, secret_name, endpoint_url="https://secretsmanager.us-east-1.amazonaws.com", region_name="us-east-1"):

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
        