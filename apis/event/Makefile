LIB_DIR              ?= ../../lib
SHARE_DIR            ?= ../../share
BIN_DIR              ?= ../../bin

PKG_NAME             ?= directorofme_event
PKG_VERSION          ?= 0.1
PKG_DEPS             ?= $(FLASK_PKG_DEPS),\
					    python-slugify>=1.2.4

FLASK_APP            ?= $(PKG_NAME):app
SERVICE_NAME         ?= $(PKG_NAME)

SERVER_ADDR          ?= $(EVENT_API_SERVICE_ADDR)
SERVER_PORT          ?= $(EVENT_API_SERVICE_PORT)
SERVER_FORKS         ?= $(EVENT_API_SERVICE_FORKS)
SERVICE_OWNER        ?= $(EVENT_API_SERVICE_USER)
SERVICE_OWNER_UID    ?= $(EVENT_API_SERVICE_UID)

PROXY_NAME           ?= $(PKG_NAME)
PROXY_HOST           ?= $(SERVER_ADDR)
PROXY_PORT           ?= $(SERVER_PORT)

API_NAME             ?= event

PSQL_DB              ?= $(EVENT_API_PSQL_DB)
PSQL_USER            ?= $(EVENT_API_PSQL_USER)
PSQL_PASSWORD        ?= $(EVENT_API_PSQL_PASSWORD)
PSQL_HOST            ?= $(EVENT_API_PSQL_HOST)

EXTRA_PYTHONPATH     ?= $(LIB_DIR)/python/core

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
