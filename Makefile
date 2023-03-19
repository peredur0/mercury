# Makefile to launch process from this project

# Docker compose environment
e_df := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/elastic/docker/docker-compose.yml
e_env := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/elastic/docker/.env
elastic_up:
	docker compose -f $(e_df) --env-file $(e_env) up -d

elastic_down:
	docker compose -f $(e_df) --env-file $(e_env) down

p_df := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/psql_db/docker/docker-compose.yml
p_env := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/psql_db/docker/.env
psql_up:
	docker compose -f $(p_df) --env-file $(p_env) up -d

psql_down:
	docker compose -f $(p_df) --env-file $(p_env) down

db_up: elastic_up psql_up
	echo "base de données lancées"

db_down: elastic_down psql_down
	echo "base de données stoppées"

# voire le code de FRED
# Statistiques
z_code := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/analyse/rech_zipf.py
zipf:
	python3 $(z_code)


# Récolte - phase1

