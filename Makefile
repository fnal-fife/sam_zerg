
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

push-all:
	docker tag sam_httpd_server bjwhitefnal/sam_httpd_server
	docker push bjwhitefnal/sam_httpd_server
	docker tag sam_station bjwhitefnal/sam_station
	docker push bjwhitefnal/sam_station
	docker tag samweb_server bjwhitefnal/samweb_server
	docker push bjwhitefnal/samweb_server

push-sam-httpd:
	docker tag sam_httpd_server bjwhitefnal/sam_httpd_server
	docker push bjwhitefnal/sam_httpd_server

push-samweb:
	docker tag sam_station bjwhitefnal/sam_station
	docker push bjwhitefnal/sam_station

push-samstation:
	docker tag samweb_server bjwhitefnal/samweb_server
	docker push bjwhitefnal/samweb_server
