LIB_DIR              ?= ../../lib
SHARE_DIR            ?= ../../share
BIN_DIR              ?= ../../bin

PKG_NAME             ?= directorofme_auth
PKG_VERSION          ?= 0.1
PKG_DEPS             ?= $(FLASK_PKG_DEPS),\
					    python-slugify>=1.2.4, \
						marshmallow-enum==1.3, \
						pycrypto>=2.6.1, \
						cryptogrophy>=2.2.2,

FLASK_APP            ?= $(PKG_NAME):app
SERVICE_NAME         ?= $(PKG_NAME)

SERVER_ADDR          ?= $(AUTH_API_SERVICE_ADDR)
SERVER_PORT          ?= $(AUTH_API_SERVICE_PORT)
SERVER_FORKS         ?= $(AUTH_API_SERVICE_FORKS)
SERVICE_OWNER        ?= $(AUTH_API_SERVICE_USER)
SERVICE_OWNER_UID    ?= $(AUTH_API_SERVICE_UID)

PROXY_NAME           ?= $(PKG_NAME)
PROXY_HOST           ?= $(SERVER_ADDR)
PROXY_PORT           ?= $(SERVER_PORT)

API_NAME             ?= auth
WEB_LOCATION         ?= $(API_WEB_LOCATION)

PSQL_DB              ?= $(AUTH_API_PSQL_DB)
PSQL_USER            ?= $(AUTH_API_PSQL_USER)
PSQL_PASSWORD        ?= $(AUTH_API_PSQL_PASSWORD)
PSQL_HOST            ?= $(AUTH_API_PSQL_HOST)

GOOGLE_CLIENT_ID     ?= $(AUTH_API_GOOGLE_CLIENT_ID)
GOOGLE_CLIENT_SECRET ?= $(AUTH_API_GOOGLE_CLIENT_SECRET)
GOOGLE_AUTH_URL      ?= $(AUTH_API_GOOGLE_AUTH_URL)
GOOGLE_TOKEN_URL     ?= $(AUTH_API_GOOGLE_TOKEN_URL)

SLACK_CLIENT_ID      ?= $(AUTH_API_SLACK_CLIENT_ID)
SLACK_APP_ID         ?= $(AUTH_API_SLACK_APP_ID)
SLACK_CLIENT_SECRET  ?= $(AUTH_API_SLACK_CLIENT_SECRET)
SLACK_AUTH_URL       ?= $(AUTH_API_SLACK_AUTH_URL)
SLACK_TOKEN_URL      ?= $(AUTH_API_SLACK_TOKEN_URL)

EXTRA_PYTHONPATH     ?= $(LIB_DIR)/python/core
FLASK_EXTRA_VARS     ?= GOOGLE_CLIENT_ID="$(GOOGLE_CLIENT_ID)" \
						GOOGLE_CLIENT_SECRET="$(GOOGLE_CLIENT_SECRET)" \
						GOOGLE_AUTH_URL="$(GOOGLE_AUTH_URL)" \
						GOOGLE_TOKEN_URL="$(GOOGLE_TOKEN_URL)" \
						SLACK_CLIENT_ID="$(AUTH_API_SLACK_CLIENT_ID)" \
						SLACK_APP_ID="$(AUTH_API_SLACK_APP_ID)" \
						SLACK_CLIENT_SECRET="$(AUTH_API_SLACK_CLIENT_SECRET)" \
						SLACK_AUTH_URL="$(AUTH_API_SLACK_AUTH_URL)" \
						SLACK_TOKEN_URL="$(AUTH_API_SLACK_TOKEN_URL)" \
						OAUTHLIB_RELAX_TOKEN_SCOPE=1 \
						JWT_PRIVATE_KEY_FILE=$(JWT_INSTALL_DIR)/$(JWT_KEY_DIR)/jwt_ec512.pem

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
