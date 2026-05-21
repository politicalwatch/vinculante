docker exec -ti vinculante-postgres-1 psql -U vinculante -d postgres -c 'DROP DATABASE vinculante'
docker exec -ti vinculante-postgres-1 psql -U vinculante -d postgres -c 'CREATE DATABASE vinculante'
docker cp ../backups/vinculante.sql vinculante-postgres-1:/tmp/vinculante.sql
docker exec -ti -e PGWASSWORD="vinculante" vinculante-postgres-1 psql -U vinculante -d vinculante -f /tmp/vinculante.sql
