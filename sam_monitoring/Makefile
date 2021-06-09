
# Docker Tasks
# Build the containers

build-all: # Build all
	docker build -t sam_station_monitor sam_station_monitor
	docker build -t sam_monitoring_server sam_monitoring_server
	docker build -t sam_landscape_stats sam_landscape_stats

build-all-nc: # Build all with --no-cache
	docker build --no-cache -t sam_station_monitor sam_station_monitor
	docker build --no-cache -t sam_monitoring_server sam_monitoring_server
	docker build --no-cache -t sam_landscape_stats sam_landscape_stats

build-sammonitoring:
	docker build -t sam_station_monitor sam_station_monitor
	docker build -t sam_monitoring_server sam_monitoring_server
	docker build -t sam_landscape_stats sam_landscape_stats

build-sammonitoring-nc:
	docker build --no-cache -t sam_station_monitor sam_station_monitor
	docker build --no-cache -t sam_monitoring_server sam_monitoring_server
	docker build --no-cache -t sam_landscape_stats sam_landscape_stats

push-all:
	docker tag sam_station_monitor bjwhitefnal/sam_station_monitor
	docker push bjwhitefnal/sam_station_monitor
	docker tag sam_monitoring_server bjwhitefnal/sam_monitoring_server
	docker push bjwhitefnal/sam_monitoring_server

push-sammonitoring:
	docker push bjwhitefnal/sam_station_monitor
	docker tag sam_monitoring_server bjwhitefnal/sam_monitoring_server
	docker push bjwhitefnal/sam_monitoring_server
