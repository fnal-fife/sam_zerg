
# Dockerfile for the SAMWeb Server

FROM python:3.6

RUN apt-get update && apt-get -y install gettext-base net-tools dnsutils && apt-get clean
RUN pip install --upgrade pip setuptools

COPY ./sam-web/requirements.txt /opt/sam/samweb_server/sam-web/requirements.txt
COPY ./config/samweb_server.conf /opt/sam/samweb_server/samweb_server.conf
COPY ./config/file_schema_mapping.json /opt/sam/samweb_server/file_schema_mapping.json
COPY ./config/uwsgi_sam_bjwhite.ini /opt/sam/samweb_server/uwsgi_sam_bjwhite.ini
COPY ./docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /opt/sam/samweb_server/sam-web

RUN pip install --no-cache-dir -r requirements.txt pytest uwsgi

ENTRYPOINT [ "/docker-entrypoint.sh" ]
