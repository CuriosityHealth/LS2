#!/bin/bash

# Check that the environment variable has been set correctly
if [ -z "$SECRETS_BUCKET_NAME" ]; then
  echo >&2 'error: missing SECRETS_BUCKET_NAME environment variable'
  exit 1
fi

# Load the S3 secrets file contents into the environment variables
eval $(aws s3 cp s3://${SECRETS_BUCKET_NAME}/db_secrets.txt - | sed 's/^/export /')
eval $(aws s3 cp s3://${SECRETS_BUCKET_NAME}/django_secrets.txt - | sed 's/^/export /')
export DJANGO_SECRET=$(aws s3 cp s3://${SECRETS_BUCKET_NAME}/django_secret_key.txt -)
export FERNET_KEYS=$(aws s3 cp s3://${SECRETS_BUCKET_NAME}/fernet_keys.txt -)

"$@"
