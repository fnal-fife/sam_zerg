
# Dockerfile for the SAM Station

#FROM docker.io/library/python:3.6
FROM registry.access.redhat.com/ubi8/python-36

USER root
RUN yum -y update && yum -y install less lsof gettext net-tools && yum clean all
RUN mkdir /var/log/sam
# Copy SAM code into image.
COPY ./sam-station /opt/sam/sam_station/sam-station
# Copy SAM configuration needs into the image
COPY ./docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /opt/sam/sam_station/sam-station

RUN pip install --upgrade pip setuptools && mkdir -p /opt/sam/sam_station/sam-station
RUN pip install -r requirements.txt pytest remote-pdb

ENTRYPOINT [ "/docker-entrypoint.sh" ]