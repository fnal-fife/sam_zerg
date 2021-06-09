
# Dockerfile for SAM Station Monitor HTTPD server

FROM httpd:2.2

RUN apt-get update -y && apt-get install -y net-tools
RUN mkdir -p /home/sam/html

COPY config/conf /usr/local/apache2/conf
COPY config/conf.d /usr/local/apache2/conf.d
COPY config/mime.types /etc/mime.types

EXPOSE 80 
CMD ["httpd", "-D", "FOREGROUND"]
