#!/usr/bin/bash

# Start docker container

db_rep="$HOME/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases"

docker compose -f "$db_rep/elastic/docker/docker-compose.yml" --env-file "$db_rep/elastic/docker/.env" up -d

docker compose -f "$db_rep/psql_db/docker/docker-compose.yml" --env-file "$db_rep/psql_db/docker/.env" up -d
