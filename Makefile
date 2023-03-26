# Makefile to launch process from this project

# *** Docker compose environment ***
e_df := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/elastic/docker/docker-compose.yml
e_env := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/elastic/docker/.env
elastic_up: $(e_df) $(e_env)
	docker compose -f $(e_df) --env-file $(e_env) up -d

elastic_down: $(e_df) $(e_env)
	docker compose -f $(e_df) --env-file $(e_env) down

p_df := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/psql_db/docker/docker-compose.yml
p_env := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/databases/psql_db/docker/.env
psql_up: $(p_df) $(p_env)
	docker compose -f $(p_df) --env-file $(p_env) up -d

psql_down: $(p_df) $(p_env)
	docker compose -f $(p_df) --env-file $(p_env) down

db_up: elastic_up psql_up
	echo "base de données lancées"

db_down: elastic_down psql_down
	echo "base de données stoppées"

# Virtual environment
VENV := py3-env
PYTHONPATH := $(shell pwd)

# cible par defaut sans argument
all: VENV

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip3 install -r $<

venv: $(VENV)/bin/activate

# Statistiques
z_code := /home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/01_programme/analyse/rech_zipf.py
zipf: $(z_code) venv
	./$(VENV)/bin/python $<

clean:
	rm -rf $(VENV)
	find . -type f -name '*.pyc' -delete

# Récolte - phase1

