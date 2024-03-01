
# Dockerfile for the SAM Apache Server

FROM docker.io/library/httpd:2.4

#RUN apt-get update -y && apt-get install -y net-tools
COPY mime.types /etc/mime.types
COPY config/conf/httpd.conf /usr/local/apache2/conf/httpd.conf
COPY config/conf.d /usr/local/apache2/conf.d

# Make /opt/sam/html DocumentRoot
RUN mkdir -p /opt/sam/html
# Make the run dir because it doesnt exist otherwise?
RUN mkdir -p /usr/local/apache2/run

EXPOSE 8483
EXPOSE 8480
CMD ["httpd", "-D", "FOREGROUND"]
