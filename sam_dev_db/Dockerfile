FROM docker.io/library/postgres:16-alpine
WORKDIR /setup
COPY initdb.sh .
COPY sam-ddl/ddl/*.sql ./
COPY sam-ddl/test_suite_data/test_suite_data.sql .
RUN ./initdb.sh
