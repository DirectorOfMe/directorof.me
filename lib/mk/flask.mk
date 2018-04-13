### THESE MUST BE PROVIDED
LIB_DIR          ?= ../
SHARE_DIR        ?= ../../share/

SERVER_ADDR      ?=
SERVER_PORT      ?=
SERVER_FORKS     ?=
SERVICE_OWNER    ?=
SERVICE_NAME     ?=

PSQL_DB          ?=
PSQL_USER        ?=
PSQL_PASSWORD    ?=
PSQL_HOST        ?=
EXTRA_PYTHONPATH ?=

TEST_PSQL_DB     ?= $(PSQL_DB)-test
TEST_MAKE        ?= PYTHONPATH=".:$(EXTRA_PYTHONPATH):$$PYTHONPATH" PSQL_DB=$(TEST_PSQL_DB) $(MAKE)
### END

### Vars we need for this make file
FLASK_APP        ?= app
MIGRATIONS       ?= migrations/
APP_DB_ENGINE    ?= postgresql://$(PSQL_USER):$(PSQL_PASSWORD)@$(PSQL_HOST)/$(PSQL_DB)

API_NAME         ?=
API_PREFIX       ?= /api/(.*)?

WEB_LOCATION     ?= $(API_PREFIX)/$(API_NAME)
WEB_SERVER_NAME  ?=

FLASK_EXTRA_VARS ?=
FLASK_ENV_VARS   ?= $(FLASK_EXTRA_VARS) \
					FLASK_APP="$(FLASK_APP)" \
				    APP_DB_ENGINE="$(APP_DB_ENGINE)" \
					API_NAME="$(API_NAME)" \
					SERVER_NAME="$(WEB_SERVER_NAME)" \
					JWT_PUBLIC_KEY_FILE=$(SHARE_DIR)/$(KEY_DIR)/jwt_ec512_pub.pem \
					JWT_PRIVATE_KEY_FILE=$(SHARE_DIR)/$(KEY_DIR)/jwt_ec512.pem
FLASK            ?= $(FLASK_ENV_VARS) PYTHONPATH=".:$(EXTRA_PYTHONPATH):$$PYTHONPATH" flask


### Service bits
RUN_FILE_TPL     ?= run.gunicorn
RUN_FILE_EXPORTS ?= FLASK_APP="$(FLASK_APP)" \
					FLASK_ENV_VARS='$(FLASK_ENV_VARS)' \
				    SERVER_ADDR="$(SERVER_ADDR)" \
					SERVER_PORT="$(SERVER_PORT)" \
					SERVER_FORKS="$(SERVER_FORKS)" \
					DAEMON_USER="$(SERVICE_OWNER)" \
					PSQL_HOST="$(PSQL_HOST)" \
					PSQL_DB="$(PSQL_DB)" \
					PSQL_USER="$(PSQL_USER)" \
					PSQL_PASSWORD="$(PSQL_PASSWORD)"

### Python pkg bits
FLASK_PKG_DEPS  ?= $(SQLALCHEMY_DEPS),\
                   directorofme_flask_restful,\
                   flask==0.12.2,\
                   flask-restful==0.3.5,\
                   flask-jwt-extended[asymmetric_crypto]>=3.8.1,\
                   flask-sqlalchemy>=2.3.2,\
                   flask-migrate>=2.1.1,\
				   gunicorn==19.7,\


.PHONY: run
run:
	$(FLASK) run -h $(SERVER_ADDR) -p $(SERVER_PORT) --reload

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

.PHONY: run-flask-test
run-flask-test:
	APP_DB_ENGINE="$(APP_DB_ENGINE)" $(MAKE) run-py-test

.PHONY: run-flask-test-with-db
run-flask-test-with-db:
	$(TEST_MAKE) postgresql && \
	$(TEST_MAKE) upgrade-db && \
	  $(TEST_MAKE) run-flask-test; rc=$$?; \
	  $(TEST_MAKE) dropdb && exit $$rc;

gunicorn-service: service/run

install-gunicorn-service: install-service

clean-gunicorn-service: clean-service

include $(LIB_DIR)/mk/service.mk
include $(LIB_DIR)/mk/psql.mk
include $(LIB_DIR)/mk/python.mk
include $(LIB_DIR)/mk/jwt.mk
