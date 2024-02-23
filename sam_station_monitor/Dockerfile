# Dockerfile for the SAM Station Monitor

FROM python:2.7

RUN apt-get update && apt-get -y install gettext-base net-tools dnsutils postgresql-client && apt-get clean
RUN pip install --upgrade pip setuptools
RUN pip install remote-pdb cherrypy==3.8.0 mako==1.0 psycopg2

# Create code directory
RUN mkdir -p /opt/sam/sam-station-monitor

# Copy the SAM Station Monitor files into the image
COPY default.cfg \
    formatters.py \
    SAMStationMonitor.py \
    station_monitor_server.py \
    StationProjectInfo.py \
    static \
    templates \
    time_functions.py \
    /opt/sam/sam-station-monitor/
EXPOSE 8081

WORKDIR /opt/sam/sam-station-monitor
CMD [ "python", "station_monitor_server.py" ]
