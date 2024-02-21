
# Dockerfile for the SAM Station

FROM docker.io/library/python:3.6

RUN apt-get update && apt-get -y install gettext-base net-tools && apt-get clean
RUN pip install --upgrade pip setuptools && mkdir -p /opt/sam/sam_station/sam-station

# Copy SAM code into image.
COPY ./sam-station /opt/sam/sam_station/sam-station

# Copy SAM configuration needs into the image
COPY ./docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /opt/sam/sam_station/sam-station

RUN pip install -r requirements.txt pytest remote-pdb

ENTRYPOINT [ "/docker-entrypoint.sh" ]