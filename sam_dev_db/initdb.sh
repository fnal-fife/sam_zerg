#!/bin/sh
PG_DB=sam_bjwhite
EXPERIMENT=sam_bjwhite
startdir=.
pg_init_dir=/docker-entrypoint-initdb.d
mkdir -p $pg_init_dir
cat > $pg_init_dir/00initialize.sql <<-EOF
CREATE USER samread;
CREATE USER samdbs;
EOF
sed "s/XXXX_ROLE_XXXX/$PG_DB/g" ${startdir}/tables.sql > $pg_init_dir/01tables.sql
sed "s/XXXX_ROLE_XXXX/$PG_DB/g" ${startdir}/primary_keys.sql > $pg_init_dir/02primary_keys.sql
sed "s/XXXX_ROLE_XXXX/$PG_DB/g" ${startdir}/indexes.sql > $pg_init_dir/03indexes.sql
sed "s/XXXX_ROLE_XXXX/$PG_DB/g" ${startdir}/foreign_keys.sql > $pg_init_dir/04foreign_keys.sql
sed "s/XXXX_ROLE_XXXX/$PG_DB/g" ${startdir}/various.sql > $pg_init_dir/05various.sql
sed "s/XXXX_ROLE_XXXX/$PG_DB/g" ${startdir}/privileges.sql > $pg_init_dir/06privileges.sql
sed "s/XXXX_ROLE_XXXX/$PG_DB/g" ${startdir}/sequences.sql > $pg_init_dir/07sequences.sql
sed -e "s/XXXX_ROLE_XXXX/$PG_DB/g" -e "s/XXXX_EXPNAME_XXXX/${EXPERIMENT}/g" ${startdir}/initial_content.sql > $pg_init_dir/08initial_content.sql
cp test_suite_data.sql $pg_init_dir/99test_suite_data.sql