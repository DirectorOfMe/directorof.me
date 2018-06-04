### THESE MUST BE PROVIDED
LIB_DIR                ?= ../ SHARE_DIR              ?= ../../share/
API_DIR                ?= ../../api/

FLASK_GROUP            ?=
FLASK_GID              ?=

JWT_INSTALL_DIR        ?= /etc
JWT_KEY_DIR            ?= jwt_keys
JWT_PUBLIC_GROUP       ?= $(FLASK_GROUP)
JWT_PRIVATE_GROUP      ?= $(AUTH_API_SERVICE_USER)
AUTH_API_DIR           ?= $(API_DIR)/auth

SERVER_ADDR            ?=
SERVER_PORT            ?=
SERVER_FORKS           ?=
SERVICE_OWNER          ?=
SERVICE_NAME           ?=
SERVICE_OWNER_GROUPS   ?= $(FLASK_GROUP)
SERVICE_OWNER_GIDS     ?= $(FLASK_GID)

PSQL_DB                ?=
PSQL_USER              ?=
PSQL_PASSWORD          ?=
PSQL_HOST              ?=
EXTRA_PYTHONPATH       ?=

TEST_PSQL_DB           ?= $(PSQL_DB)-test
TEST_MAKE              ?= PYTHONPATH=".:$(EXTRA_PYTHONPATH):$$PYTHONPATH" PSQL_DB=$(TEST_PSQL_DB) $(MAKE)
### END
### TODO: INSTALL REDOC STATIC HTML PAGE POINTING TO THIS SERVICE

### Vars we need for this make file
FLASK_APP              ?= app
MIGRATIONS             ?= migrations/
APP_DB_ENGINE          ?= postgresql://$(PSQL_USER):$(PSQL_PASSWORD)@$(PSQL_HOST)/$(PSQL_DB)

API_NAME               ?=
API_PREFIX             ?= /api/(.*)?

APP_NAME               ?=
APP_PREFIX             ?= /app

API_WEB_LOCATION       ?= $(API_PREFIX)/$(API_NAME)
APP_WEB_LOCATION       ?= $(APP_PREFIX)/$(APP_NAME)

WEB_LOCATION           ?=
WEB_SERVER_NAME        ?=

FLASK_EXTRA_VARS       ?=
FLASK_ENV_VARS         ?= $(FLASK_EXTRA_VARS) \
		                  FLASK_APP="$(FLASK_APP)" \
				          APP_DB_ENGINE="$(APP_DB_ENGINE)" \
				     	  API_NAME="$(API_NAME)" \
					      SERVER_NAME="$(WEB_SERVER_NAME)" \
					      JWT_PUBLIC_KEY_FILE=$(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/jwt_ec512_pub.pem \
						  PUSH_REFRESH_TOKEN_FILE=/etc/push_tokens/push_refresh_token \
						  PUSH_REFRESH_CSRF_TOKEN_FILE=/etc/push_tokens/push_refresh_csrf_token
FLASK                  ?= $(FLASK_ENV_VARS) PYTHONPATH=".:$(EXTRA_PYTHONPATH):$$PYTHONPATH" flask


### Service bits
RUN_FILE_TPL           ?= run.gunicorn
RUN_FILE_EXPORTS       ?= FLASK_APP="$(FLASK_APP)" \
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
FLASK_PKG_DEPS          ?= $(SQLALCHEMY_DEPS),\
                           directorofme,\
                           flask==1.0,\
                           flask-restful==0.3.5,\
                           flask-jwt-extended[asymmetric_crypto]>=3.8.1,\
                           flask-sqlalchemy>=2.3.2,\
                           flask-migrate>=2.1.1,\
				           flask-marshmallow==0.8.0,\
				           apispec==0.35.0,\
				           gunicorn==19.7,\
					       requests-oauthlib>=0.8.0,\
					       furl>=1.0.1



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

.PHONY: flask-command
flask-command:
	@if [ -z "$(FLASK_COMMAND)" ]; then \
		echo "set FLASK_COMMAND and re-run"; exit 1; \
	else \
		$(FLASK) $(FLASK_COMMAND); \
    fi

.PHONY: run-flask-test
run-flask-test:
	$(FLASK_ENV_VARS) $(MAKE) run-py-test

.PHONY: run-flask-test-with-db
run-flask-test-with-db:
	$(TEST_MAKE) postgresql && \
	$(TEST_MAKE) upgrade-db && \
	  $(TEST_MAKE) run-flask-test; rc=$$?; \
	  $(TEST_MAKE) dropdb && exit $$rc;

gunicorn-service: service/run

install-gunicorn-service: install-jwt_keys install-service

clean-gunicorn-service: clean-service

$(SHARE_DIR)/$(JWT_KEY_DIR)/.d:
	install -d -m 700 $(SHARE_DIR)/$(JWT_KEY_DIR)
	touch $@

$(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512.pem: $(SHARE_DIR)/$(JWT_KEY_DIR)/.d
	[ -f $@ ] || openssl ecparam -genkey -name secp521r1 -noout -out $@

$(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512_pub.pem: $(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512.pem
	[ -f $@ ] || openssl ec -in $< -outform PEM -pubout -out $@


$(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/jwt_ec512.pem: $(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/.d \
											     $(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512.pem
	sudo install -o root -g $(JWT_PRIVATE_GROUP) -m 0640 $(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512.pem $@

$(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/jwt_ec512_pub.pem: $(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/.d \
												     $(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512_pub.pem
	sudo install -o root -g $(JWT_PUBLIC_GROUP) -m 0640 $(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512_pub.pem $@

$(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/.d:
	sudo install -g root -o root -m 0755 -d $(JWT_INSTALL_DIR)/$(JWT_KEY_DIR) && sudo touch $@

.PHONY: jwt_keys
jwt_keys: $(SHARE_DIR)/$(JWT_KEY_DIR)/jwt_ec512_pub.pem

.PHONY: install-jwt_keys
install-jwt_keys: $(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/jwt_ec512.pem \
				  $(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/jwt_ec512_pub.pem

# NOTE: This is not hooked up to the generic clean intentionally. Replacing these keys has big consequences.
.PHONY: clean-jwt_keys
clean-jwt_keys:
	rm -f $(SHARE_DIR)/$(JWT_KEY_DIR)

/etc/push_tokens/%: push_tokens/% /etc/push_tokens/.d
	sudo install -o root -g $(FLASK_GROUP) -m 0640 $< $@

/etc/push_tokens/.d:
	sudo install -o root -g $(FLASK_GROUP) -m 0750 -d /etc/push_tokens/ && sudo touch $@

push_tokens/push_refresh_token: push_tokens/.d
	@FLASK_COMMAND=push_refresh_token $(SUBMAKE) flask-command $(AUTH_API_DIR) | awk '$$1 !~ /make/ { print; }' > $@.tmp && mv $@.tmp $@

push_tokens/push_refresh_csrf_token: push_tokens/push_refresh_token push_tokens/.d
	@FLASK_COMMAND=push_refresh_csrf_token $(SUBMAKE) flask-command $(AUTH_API_DIR) < $< | awk '$$1 !~ /make/ { print; }' > $@.tmp && mv $@.tmp $@

push_tokens/.d:
	install -d push_tokens && touch $@

.PHONY: push-tokens
push-tokens: push_tokens/push_refresh_token push_tokens/push_refresh_csrf_token push_tokens/.d

.PHONY: install-push-tokens
install-push-tokens: /etc/push_tokens/push_refresh_token /etc/push_tokens/push_refresh_csrf_token

.PHONY: clean-push-tokens
clean-push-tokens:
	rm -rf push_tokens/


include $(LIB_DIR)/mk/service.mk
include $(LIB_DIR)/mk/psql.mk
include $(LIB_DIR)/mk/python.mk
