### NEEDS TO BE TEMPLATED INTO app.py
PSQL_DB         ?= dom
PSQL_USER       ?= dom
PSQL_PASS       ?= password
PSQL_HOST       ?= loclahost
FLASK_APP       ?= app
APP_DB_ENGINE   ?= "postgresql:///$(PSQL_USER):$(PSQL_PASS)@$(PSQL_HOST)/$(PSQL_DB)"
FLASK           ?= FLASK_APP="$(FLASK_APP)" APP_DB_ENGINE="$(APP_DB_ENGINE)" flask

.PHONY: shell
shell:
	$(FLASK) $@

.PHONY: migrate
migrate:
	$(FLASK) $@
