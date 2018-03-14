LIB_DIR              ?= ../../lib
SHARE_DIR            ?= ../../share
BIN_DIR              ?= ../../bin

PKG_NAME             ?= directorofme_auth
PKG_VERSION          ?= 0.1
PKG_DEPS             ?= directorofme,\
				        $(FLASK_PKG_DEPS),\
					    python-slugify>=1.2.4,\
						requests-oauthlib>=0.8.0,

FLASK_APP            ?= $(PKG_NAME):app
SERVICE_NAME         ?= $(PKG_NAME)

SERVER_ADDR          ?= $(AUTH_SERVICE_ADDR)
SERVER_PORT          ?= $(AUTH_SERVICE_PORT)
SERVER_FORKS         ?= $(AUTH_SERVICE_FORKS)
SERVICE_OWNER        ?= $(AUTH_SERVICE_USER)
SERVICE_OWNER_UID    ?= $(AUTH_SERVICE_UID)

PROXY_NAME           ?= $(PKG_NAME)
PROXY_HOST           ?= $(SERVER_ADDR)
PROXY_PORT           ?= $(SERVER_PORT)

API_NAME             ?= auth

PSQL_DB              ?= $(AUTH_PSQL_DB)
PSQL_USER            ?= $(AUTH_PSQL_USER)
PSQL_PASSWORD        ?= $(AUTH_PSQL_PASSWORD)
PSQL_HOST            ?= $(AUTH_PSQL_HOST)

GOOGLE_CLIENT_ID     ?= $(AUTH_GOOGLE_CLIENT_ID)
GOOGLE_CLIENT_SECRET ?= $(AUTH_GOOGLE_CLIENT_SECRET)
GOOGLE_AUTH_URL      ?= $(AUTH_GOOGLE_AUTH_URL)
GOOGLE_TOKEN_URL     ?= $(AUTH_GOOGLE_TOKEN_URL)

FLASK_EXTRA_VARS     ?= GOOGLE_CLIENT_ID="$(GOOGLE_CLIENT_ID)" \
						GOOGLE_CLIENT_SECRET="$(GOOGLE_CLIENT_SECRET)" \
						GOOGLE_AUTH_URL="$(GOOGLE_AUTH_URL)" \
						GOOGLE_TOKEN_URL="$(GOOGLE_TOKEN_URL)" \


.PHONY: default
default: build-setup-py gunicorn-service proxy.conf

.PHONY: clean
clean: clean-setup-py clean-postgresql clean-gunicorn-service clean-proxy.conf

.PHONY: install
install: default install-setup-py install-gunicorn-service install-proxy.conf

.PHONY: dev
dev: postgresql

.PHONY: test
test: run-flask-test-with-db

include $(LIB_DIR)/mk/flask.mk
include $(LIB_DIR)/mk/web.mk
include ../../directorofme.conf
