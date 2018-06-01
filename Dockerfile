FROM python:3.6
MAINTAINER James Kizer <james@curiosityhealth.com>

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get -y install python curl unzip && cd /tmp && \
    curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip" && \
    unzip awscli-bundle.zip && \
    ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws && \
    rm awscli-bundle.zip && rm -rf awscli-bundle

#Add LDAP Support
RUN apt-get -y install build-essential python3-dev \
  libldap2-dev libsasl2-dev ldap-utils

ADD . /src/

RUN pip install -r /src/requirements.txt

# SECRET KEY
# This MUST be replaced by mounting an actual secret file here
# LS2 will NOT load until it is replaced
# Generate a key file with "openssl rand -base64 n -out secret.txt"
# Note that this CAN be rotated with little (not none) impact to system functionality
# see https://docs.djangoproject.com/en/2.0/ref/settings/#secret-key for more details
RUN mkdir /etc/ls2
RUN touch /etc/ls2/django_secrets.txt
RUN touch /etc/ls2/django_secret_key.txt
RUN touch /etc/ls2/fernet_keys.txt
RUN mkdir /etc/ls2/settings
RUN touch /etc/ls2/settings/databases.json
RUN touch /etc/ls2/settings/migration_databases.json

RUN mkdir /logs

WORKDIR /src
