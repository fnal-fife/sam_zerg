
# podman Tasks
# Build the containers

build-all: # Build all
	podman build -t sam_httpd_server sam_httpd_server
	podman build -t sam_station sam_station
	podman build -t samweb_server samweb_server

build-all-nc: # Build all with --no-cache
	podman build --no-cache -t sam_httpd_server sam_httpd_server
	podman build --no-cache -t sam_station sam_station
	podman build --no-cache -t samweb_server samweb_server

build-samhttpd:
	podman build -t sam_httpd_server sam_httpd_server

build-samhttpd-nc:
	podman build --no-cache -t sam_httpd_server sam_httpd_server

build-samweb:
	podman build -t samweb_server samweb_server

build-samweb-nc:
	podman build --no-cache -t samweb_server samweb_server

build-samstation:
	podman build -t sam_station sam_station

build-samstation-nc:
	podman build --no-cache -t sam_station sam_station
