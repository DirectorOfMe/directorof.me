SERVICE_OWNER            ?= $(CALENDAR_SERVICE_USER)
SERVICE_OWNER_UID        ?= $(CALENDAR_SERVICE_UID)

LIB_DIR                  ?= ../../lib
SHARE_DIR                ?= ../../share
BIN_DIR                  ?= ../../bin

PKG_NAME                 ?= directorofme_calendar
PKG_VERSION              ?= 0.1

PKG_DEPS                 ?= $(FLASK_PKG_DEPS),\
						    pycrypto>=2.6.1,\
					        python-slugify>=1.2.4,\
					    	requests-oauthlib>=0.8.0,\
					    	pybars3>=0.9.3

FLASK_APP                ?= $(PKG_NAME):app
SERVICE_NAME             ?= $(PKG_NAME)

SERVER_ADDR              ?= $(CALENDAR_SERVICE_ADDR)
SERVER_PORT              ?= $(CALENDAR_SERVICE_PORT)
SERVER_FORKS             ?= $(CALENDAR_SERVICE_FORKS)
SERVICE_OWNER            ?= $(CALENDAR_SERVICE_USER)
SERVICE_OWNER_UID        ?= $(CALENDAR_SERVICE_UID)

GOOGLE_CLIENT_ID         ?= $(CALENDAR_GOOGLE_CLIENT_ID)
GOOGLE_CLIENT_SECRET     ?= $(CALENDAR_GOOGLE_CLIENT_SECRET)
GOOGLE_AUTH_URL          ?= $(CALENDAR_GOOGLE_AUTH_URL)
GOOGLE_TOKEN_URL         ?= $(CALENDAR_GOOGLE_TOKEN_URL)

SLACK_APP_ID             ?= $(CALENDAR_SLACK_APP_ID)

PROXY_NAME               ?= $(PKG_NAME)
PROXY_HOST               ?= $(SERVER_ADDR)
PROXY_PORT               ?= $(SERVER_PORT)

API_NAME                 ?= calendar
WEB_LOCATION             ?= $(API_WEB_LOCATION)

# Ideally we just need the client id here and nothing else

EXTRA_PYTHONPATH         ?= $(LIB_DIR)/python/core
FLASK_EXTRA_VARS         ?= CALENDAR_PRIVATE_KEY_FILE=/etc/directorofme_calendar/calendar.pem \
					    	CALENDAR_PUBLIC_KEY_FILE=/etc/directorofme_calendar/calendar_pub.pem \
							GOOGLE_CLIENT_ID="$(GOOGLE_CLIENT_ID)" \
							GOOGLE_CLIENT_SECRET="$(GOOGLE_CLIENT_SECRET)" \
							GOOGLE_AUTH_URL="$(GOOGLE_AUTH_URL)" \
							GOOGLE_TOKEN_URL="$(GOOGLE_TOKEN_URL)" \
							SLACK_APP_ID="$(SLACK_APP_ID)"

.PHONY: default
default: build-setup-py gunicorn-service proxy.conf crypto/calendar.pem

.PHONY: clean
clean: clean-setup-py clean-gunicorn-service clean-proxy.conf

.PHONY: install
install: default install-setup-py install-gunicorn-service install-proxy.conf \
		 /etc/directorofme_calendar/calendar_pub.pem

.PHONY: test
test: run-flask-test

/etc/directorofme_calendar/calendar.pem: crypto/calendar.pem /etc/directorofme_calendar/.d
	sudo install -o root -g $(SERVICE_OWNER) -m 0640 crypto/calendar.pem $@

/etc/directorofme_calendar/calendar_pub.pem: crypto/calendar_pub.pem /etc/directorofme_calendar/calendar.pem
	sudo install -o root -g $(FLASK_GROUP) -m 0640 crypto/calendar_pub.pem $@

/etc/directorofme_calendar/.d:
	sudo install -g root -o root -m 0755 -d /etc/directorofme_calendar && sudo touch $@

crypto/.d:
	install -d -m 700 crypto
	touch $@

crypto/calendar.pem: crypto/.d
	[ -f $@ ] || openssl genrsa -out $@ 4096

crypto/calendar_pub.pem: crypto/calendar.pem
	[ -f $@ ] || openssl rsa -in $< -outform PEM -pubout -out $@

include $(LIB_DIR)/mk/flask.mk
include $(LIB_DIR)/mk/web.mk
include ../../directorofme.conf
