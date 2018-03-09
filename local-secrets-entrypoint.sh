#!/bin/bash

# Check that the environment variable has been set correctly

# Load the secrets file contents into the environment variables
eval $(cat /etc/ls2/django_secrets.txt | sed 's/^/export /')
export DATABASE_JSON_STRING=$(cat /etc/ls2/settings/databases.json)
export DJANGO_SECRET=$(cat /etc/ls2/django_secret_key.txt)
export FERNET_KEYS=$(cat /etc/ls2/fernet_keys.txt)

# Call the command
"$@"
