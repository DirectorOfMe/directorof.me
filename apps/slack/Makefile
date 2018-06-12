SERVICE_OWNER            ?= $(SLACK_SERVICE_USER)
SERVICE_OWNER_UID        ?= $(SLACK_SERVICE_UID)

LIB_DIR                  ?= ../../lib
SHARE_DIR                ?= ../../share
BIN_DIR                  ?= ../../bin

PKG_NAME                 ?= directorofme_slack
PKG_VERSION              ?= 0.1

PKG_DEPS                 ?= $(FLASK_PKG_DEPS),\
						    pycrypto>=2.6.1,\
					        python-slugify>=1.2.4,\
					    	requests-oauthlib>=0.8.0,\
					    	pybars3>=0.9.3

FLASK_APP                ?= $(PKG_NAME):app
SERVICE_NAME             ?= $(PKG_NAME)

SERVER_ADDR              ?= $(SLACK_SERVICE_ADDR)
SERVER_PORT              ?= $(SLACK_SERVICE_PORT)
SERVER_FORKS             ?= $(SLACK_SERVICE_FORKS)
SERVICE_OWNER            ?= $(SLACK_SERVICE_USER)
SERVICE_OWNER_UID        ?= $(SLACK_SERVICE_UID)

PROXY_NAME               ?= $(PKG_NAME)
PROXY_HOST               ?= $(SERVER_ADDR)
PROXY_PORT               ?= $(SERVER_PORT)

API_NAME                 ?= slack
WEB_LOCATION             ?= $(API_WEB_LOCATION)

# Ideally we just need the client id here and nothing else
SLACK_APP_ID             ?= $(SLACK_SLACK_APP_ID)
SLACK_CLIENT_ID          ?= $(SLACK_SLACK_CLIENT_ID)
SLACK_CLIENT_SECRET      ?= $(SLACK_SLACK_CLIENT_SECRET)
SLACK_AUTH_URL           ?= $(SLACK_SLACK_AUTH_URL)
SLACK_TOKEN_URL          ?= $(SLACK_SLACK_TOKEN_URL)
SLACK_VERIFICATION_TOKEN ?= $(SLACK_SLACK_VERIFICATION_TOKEN)

EXTRA_PYTHONPATH         ?= $(LIB_DIR)/python/core
FLASK_EXTRA_VARS         ?= SLACK_CLIENT_ID="$(SLACK_CLIENT_ID)" \
					    	SLACK_CLIENT_SECRET="$(SLACK_CLIENT_SECRET)" \
					    	SLACK_AUTH_URL="$(SLACK_AUTH_URL)" \
					    	SLACK_TOKEN_URL="$(SLACK_TOKEN_URL)" \
							SLACK_APP_ID="$(SLACK_APP_ID)" \
							SLACK_VERIFICATION_TOKEN="$(SLACK_VERIFICATION_TOKEN)" \
					    	OAUTHLIB_RELAX_TOKEN_SCOPE=1 \
					    	SLACK_PRIVATE_KEY_FILE=/etc/directorofme_slack/slack.pem \
					    	SLACK_PUBLIC_KEY_FILE=/etc/directorofme_slack/slack_pub.pem

.PHONY: default
default: build-setup-py gunicorn-service proxy.conf crypto/slack.pem

.PHONY: clean
clean: clean-setup-py clean-gunicorn-service clean-proxy.conf

.PHONY: install
install: default install-setup-py install-gunicorn-service install-proxy.conf \
		 /etc/directorofme_slack/slack_pub.pem

.PHONY: test
test: run-flask-test

/etc/directorofme_slack/slack.pem: crypto/slack.pem /etc/directorofme_slack/.d
	sudo install -o root -g $(SERVICE_OWNER) -m 0640 crypto/slack.pem $@

/etc/directorofme_slack/slack_pub.pem: crypto/slack_pub.pem /etc/directorofme_slack/slack.pem
	sudo install -o root -g $(FLASK_GROUP) -m 0640 crypto/slack_pub.pem $@

/etc/directorofme_slack/.d:
	sudo install -g root -o root -m 0755 -d /etc/directorofme_slack && sudo touch $@

crypto/.d:
	install -d -m 700 crypto
	touch $@

crypto/slack.pem: crypto/.d
	[ -f $@ ] || openssl genrsa -out $@ 4096
crypto/slack_pub.pem: crypto/slack.pem
	[ -f $@ ] || openssl rsa -in $< -outform PEM -pubout -out $@

include $(LIB_DIR)/mk/flask.mk
include $(LIB_DIR)/mk/web.mk
include ../../directorofme.conf
