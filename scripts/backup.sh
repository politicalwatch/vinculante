docker exec -ti vinculante-postgres-1 rm /tmp/vinculante.sql
docker exec -ti -e PGWASSWORD="vinculante" vinculante-postgres-1 pg_dump -U vinculante -d vinculante -f /tmp/vinculante.sql
docker cp vinculante-postgres-1:/tmp/vinculante.sql ../backups/
