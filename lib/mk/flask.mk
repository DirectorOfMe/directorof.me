### NEEDS TO BE TEMPLATED INTO app.py
PSQL_DB         ?= dom
PSQL_USER       ?= dom
PSQL_PASS       ?= password
PSQL_HOST       ?= localhost
FLASK_APP       ?= app
MIGRATIONS      ?= migrations/
APP_DB_ENGINE   ?= "postgresql://$(PSQL_USER):$(PSQL_PASS)@$(PSQL_HOST)/$(PSQL_DB)"
FLASK           ?= FLASK_APP="$(FLASK_APP)" APP_DB_ENGINE="$(APP_DB_ENGINE)" flask

.PHONY: shell
shell:
	$(FLASK) $@

.PHONY: migrate
migrate:
	{ [ -d $(MIGRATIONS) ] || $(FLASK) db init; } && $(FLASK) db $@

.PHONY: upgrade-db
upgrade-db:
	$(FLASK) db upgrade

.PHONY: db
db:
	if [ -z "$(DB_COMMAND)" ]; then \
	  echo "set DB_COMMAND and re-run"; exit 1; \
	else \
		$(FLASK) db $(DB_COMMAND); \
	fi
