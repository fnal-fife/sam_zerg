
# Dockerfile for the SAM Nginx Server

FROM nginx

COPY ./cert /opt/sam/private/cert
COPY ./config/nginx.conf /etc/nginx/nginx.conf
COPY ./docker-entrypoint.sh /docker-entrypoint.sh

EXPOSE 8480
ENTRYPOINT [ "/docker-entrypoint.sh" ]
