#!/bin/bash

# Check that the environment variable has been set correctly

# Load the secrets file contents into the environment variables
eval $(cat /etc/ls2/django_secrets.txt | sed 's/^/export /')
eval $(cat /etc/ls2/db_secrets.txt | sed 's/^/export /')
export DJANGO_SECRET=$(cat /etc/ls2/django_secret_key.txt)

# Call the command
"$@"
