LIB_DIR            ?= ../../lib
SHARE_DIR          ?= ../../share
BIN_DIR            ?= ../../bin

TEST_PSQL_DB       ?= test
TEST_MAKE          ?= PSQL_DB=$(TEST_PSQL_DB) $(MAKE)

PKG_NAME           ?= directorofme_auth
PKG_VERSION        ?= 0.1
PKG_DEPS           ?= directorofme,\
				      $(FLASK_PKG_DEPS),\
					  python-slugify>=1.2.4,\

FLASK_APP          ?= $(PKG_NAME):app
SERVICE_NAME       ?= $(PKG_NAME)

.PHONY: default
default: build-setup-py postgresql gunicorn-service

.PHONY: clean
clean: clean-setup-py clean-postgresql clean-gunicorn-service

.PHONY: install
install: default install-setup-py  install-gunicorn-service

.PHONY:
test:
	$(TEST_MAKE) postgresql && \
	$(TEST_MAKE) upgrade-db && \
	  $(TEST_MAKE) run-flask-test; rc=$$?; \
	  $(TEST_MAKE) dropdb && exit $$rc;

include $(LIB_DIR)/mk/python.mk
include $(LIB_DIR)/mk/psql.mk
include $(LIB_DIR)/mk/flask.mk
