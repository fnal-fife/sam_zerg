
# Dockerfile for the SAM Station

FROM docker.io/library/python:3.6

RUN apt-get update && apt-get -y install gettext-base net-tools && apt-get clean
RUN pip install --upgrade pip setuptools && mkdir -p /opt/sam/sam_station/sam-station

COPY ./sam-station/requirements.txt /opt/sam/sam_station/sam-station
COPY ./config/bjwhite_test_config.yaml /opt/sam/sam_station/sam_station_config.yaml
COPY ./config/bjwhite_test_file_schema_mapping.json /opt/sam/sam_station/file_schema_mapping.json
COPY ./config/bjwhite_test_location_map.yaml /opt/sam/sam_station/location_map.yaml
COPY ./docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /opt/sam/sam_station/sam-station

RUN pip install -r requirements.txt pytest remote-pdb

ENTRYPOINT [ "/docker-entrypoint.sh" ]
