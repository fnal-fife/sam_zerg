
# Dockerfile for the SAM Station

FROM python:3.6

COPY sam-station /opt/sam/sam_station

RUN pip install --upgrade pip setuptools
RUN cd /opt/sam/sam_station && pip install -e .

CMD [ "sam_station", "/opt/samweb/sam_station_config.yaml" ]
