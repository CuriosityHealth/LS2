FROM python:3.6

ENV PYTHONUNBUFFERED 1

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
RUN touch /etc/ls2/db_secret.txt

RUN mkdir /logs

WORKDIR /src
