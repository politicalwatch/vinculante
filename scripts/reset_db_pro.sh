docker compose -f ../docker-compose-pro.yml exec postgres psql -U vinculante -d postgres -c 'DROP DATABASE vinculante'
docker compose -f ../docker-compose-pro.yml exec postgres psql -U vinculante -d postgres -c 'CREATE DATABASE vinculante'
docker compose -f ../docker-compose-pro.yml exec postgres psql -U vinculante -d postgres -c 'CREATE EXTENSION IF NOT EXISTS vector'