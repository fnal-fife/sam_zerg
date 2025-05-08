# Dockerfile for the SAM tape label updater CronJob
FROM registry.access.redhat.com/ubi8/python-36

USER root
RUN yum -y update && yum clean all
RUN pip install psycopg2-binary
# Copy SAM tape label updater into image.
COPY ./update_sam_file_tape_status.py /opt/sam/
# Copy SAM client code into image
COPY ./samweb-client /opt/sam/

ENV PATH="/opt/sam/sam-web-client/bin:${PATH}"
ENV PYTHONPATH="/opt/sam/sam-web-client/python:${PYTHONPATH}"

WORKDIR /opt/sam/
