
# Dockerfile for the SAM Apache Server

FROM httpd

COPY config/conf/httpd.conf /usr/local/apache2/conf/httpd.conf
COPY config/conf.d /usr/local/apache2/conf.d

EXPOSE 8483
CMD [ "apachectl", "start" ]
