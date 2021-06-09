# Dockerfile of the SAM Landscapes Statistics microservice

FROM python:2.7

RUN apt-get update && apt-get -y install gettext-base net-tools dnsutils postgresql-client && apt-get clean
RUN pip install --upgrade pip setuptools psycopg2

# Create a place, and move the code into it
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
COPY ./sam_stats_graphite.py /sam_stats_graphite.py

ENTRYPOINT [ "/docker-entrypoint.sh" ]
