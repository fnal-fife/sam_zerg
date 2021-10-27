
# Docker Tasks
# Build the containers

build-all: # Build all
	docker build -t sam_httpd_server sam_httpd_server
	docker build -t sam_station sam_station
	docker build -t samweb_server samweb_server

build-all-nc: # Build all with --no-cache
	docker build --no-cache -t sam_httpd_server sam_httpd_server
	docker build --no-cache -t sam_station sam_station
	docker build --no-cache -t samweb_server samweb_server

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
