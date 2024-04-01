
# podman Tasks
# Build the containers

build-all: # Build all
	podman build -t sam_nginx_server sam_nginx_server
	podman build -t sam_station sam_station
	podman build -t samweb_server samweb_server
	podman build -t sam_dev_db sam_dev_db
	podman build -t sam_station_monitor sam-station-monitor/sam_station_monitor

build-all-nc: # Build all with --no-cache
	podman build --no-cache -t sam_nginx_server sam_nginx_server
	podman build --no-cache -t sam_station sam_station
	podman build --no-cache -t samweb_server samweb_server
	podman build --no-cache -t sam_dev_db sam_dev_db
	podman build --no-cache -t sam_station_monitor sam-station-monitor/sam_station_monitor

build-samnginx:
	podman build -t sam_nginx_server sam_nginx_server

build-samnginx-nc:
	podman build --no-cache -t sam_nginx_server sam_nginx_server

build-samweb:
	podman build -t samweb_server samweb_server

build-samweb-nc:
	podman build --no-cache -t samweb_server samweb_server

build-samstation:
	podman build -t sam_station sam_station

build-samstation-nc:
	podman build --no-cache -t sam_station sam_station

build-samdb:
	podman build -t sam_dev_db sam_dev_db

build-samdb-nc:
	podman build --no-cache -t sam_dev_db sam_dev_db

build-sammonitoring:
	podman build -t sam_station_monitor sam-station-monitor/sam_station_monitor

build-sammonitoring-nc:
	podman build --no-cache -t sam_station_monitor sam-station-monitor/sam_station_monitor


push-all:
	podman tag sam_nginx_server imageregistry.fnal.gov/sam-zerg/sam-nginx-server:latest
	podman push imageregistry.fnal.gov/sam-zerg/sam-nginx-server:latest
	podman tag samweb_server imageregistry.fnal.gov/sam-zerg/samweb-server:latest
	podman push imageregistry.fnal.gov/sam-zerg/samweb-server:latest
	podman tag sam_station imageregistry.fnal.gov/sam-zerg/sam-station:latest
	podman push imageregistry.fnal.gov/sam-zerg/sam-station:latest
	podman tag sam_station_monitor imageregistry.fnal.gov/sam-zerg/sam-station-monitor:latest
	podman push imageregistry.fnal.gov/sam-zerg/sam-station-monitor:latest
