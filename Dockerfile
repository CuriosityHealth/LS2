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

RUN mkdir /etc/ls2
RUN mkdir /etc/ls2/settings
RUN touch /etc/ls2/settings/config.json

RUN mkdir /logs

WORKDIR /src
