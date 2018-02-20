#!/bin/bash

# Check that the environment variable has been set correctly
if [ -z "$SECRETS_FILE" ]; then
  echo >&2 'error: missing SECRETS_FILE environment variable'
  exit 1
fi

if [ -z "$DJANGO_SECRET_FILE" ]; then
  echo >&2 'error: missing DJANGO_SECRET_FILE environment variable'
  exit 1
fi

# Load the secrets file contents into the environment variables
eval $(cat ${SECRETS_FILE} | sed 's/^/export /')
export DJANGO_SECRET=$(cat ${DJANGO_SECRET_FILE})

# Call the command
"$@"
