
# Docker Tasks
# Build the containers

build-all: # Build all
	docker build -t sam_httpd_server sam_httpd_server
	docker build -t sam_station sam_station
	docker build -t samweb_server samweb_server
	docker build -t sam_station_monitor sam_monitoring/sam_station_monitor
	docker build -t sam_monitoring_server sam_monitoring/sam_monitoring_server
	docker build -t sam_landscape_stats sam_monitoring/sam_landscape_stats

build-all-nc: # Build all with --no-cache
	docker build --no-cache -t sam_httpd_server sam_httpd_server
	docker build --no-cache -t sam_station sam_station
	docker build --no-cache -t samweb_server samweb_server
	docker build --no-cache -t sam_station_monitor sam_monitoring/sam_station_monitor
	docker build --no-cache -t sam_monitoring_server sam_monitoring/sam_monitoring_server
	docker build --no-cache -t sam_landscape_stats sam_monitoring/sam_landscape_stats

build-sammonitoring:
	docker build -t sam_station_monitor sam_monitoring/sam_station_monitor
	docker build -t sam_monitoring_server sam_monitoring/sam_monitoring_server
	docker build -t sam_landscape_stats sam_monitoring/sam_landscape_stats

build-sammonitoring-nc:
	docker build --no-cache -t sam_station_monitor sam_monitoring/sam_station_monitor
	docker build --no-cache -t sam_monitoring_server sam_monitoring/sam_monitoring_server
	docker build --no-cache -t sam_landscape_stats sam_monitoring/sam_landscape_stats

build-samhttpd:
	docker build -t sam_httpd_server sam_httpd_server

build-samhttpd-nc:
	docker build --no-cache -t sam_httpd_server sam_httpd_server

build-samweb:
	docker build -t samweb_server samweb_server

build-samweb-nc:
	docker build --no-cache -t samweb_server samweb_server

build-samstation:
	docker build -t sam_station sam_station

build-samstation-nc:
	docker build --no-cache -t sam_station sam_station

push-all:
	docker tag sam_httpd_server bjwhitefnal/sam_httpd_server
	docker push bjwhitefnal/sam_httpd_server
	docker tag sam_station bjwhitefnal/sam_station
	docker push bjwhitefnal/sam_station
	docker tag samweb_server bjwhitefnal/samweb_server
	docker push bjwhitefnal/samweb_server
	docker tag sam_station_monitor bjwhitefnal/sam_station_monitor
	docker push bjwhitefnal/sam_station_monitor
	docker tag sam_monitoring_server bjwhitefnal/sam_monitoring_server
	docker push bjwhitefnal/sam_monitoring_server

push-sam-httpd:
	docker tag sam_httpd_server bjwhitefnal/sam_httpd_server
	docker push bjwhitefnal/sam_httpd_server

push-samweb:
	docker tag sam_station bjwhitefnal/sam_station
	docker push bjwhitefnal/sam_station

push-samstation:
	docker tag samweb_server bjwhitefnal/samweb_server
	docker push bjwhitefnal/samweb_server

push-sammonitoring:
	docker push bjwhitefnal/sam_station_monitor
	docker tag sam_monitoring_server bjwhitefnal/sam_monitoring_server
	docker push bjwhitefnal/sam_monitoring_server
