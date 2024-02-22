
# podman Tasks
# Build the containers

apply:
	kubectl apply -k .

build-all-nc: # Build all with --no-cache
	podman build --no-cache -t sam_httpd_server sam_httpd_server
	podman build --no-cache -t sam_station sam_station
	podman build --no-cache -t samweb_server samweb_server
	podman build --no-cache -t sam_dev_db sam_dev_db

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

build-samdb:
	podman build -t sam_dev_db sam_dev_db

build-samdb-nc:
	podman build --no-cache -t sam_dev_db sam_dev_db

push-all:
	podman tag sam_httpd_server imageregistry.fnal.gov/sam-zerg/sam-httpd-server:latest
	podman push imageregistry.fnal.gov/sam-zerg/sam-httpd-server:latest
	podman tag samweb_server imageregistry.fnal.gov/sam-zerg/samweb-server:latest
	podman push imageregistry.fnal.gov/sam-zerg/samweb-server:latest
	podman tag sam_station imageregistry.fnal.gov/sam-zerg/sam-station:latest
	podman push imageregistry.fnal.gov/sam-zerg/sam-station:latest
