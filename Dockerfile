FROM python:3.6

ENV PYTHONUNBUFFERED 1

ADD . /src/

RUN pip install -r /src/requirements.txt

RUN mkdir /logs

WORKDIR /src
