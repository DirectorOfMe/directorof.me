LIB_DIR            ?= ../../lib
SHARE_DIR          ?= ../../share
FLASK_APP          ?= directorofme_auth:app

TEST_PSQL_DB       ?= test
TEST_MAKE          ?= PSQL_DB=$(TEST_PSQL_DB) $(MAKE)

.PHONY: default
default: build-setup-py postgresql

.PHONY: clean
clean: clean-setup-py clean-postgresql

.PHONY: install
install: default install-setup-py

.PHONY:
test:
	$(TEST_MAKE) postgresql;
	$(TEST_MAKE) upgrade-db; \
	  $(TEST_MAKE) run-flask-test; rc=$$?; \
	  $(TEST_MAKE) dropdb && exit $$rc;

include $(LIB_DIR)/mk/python.mk
include $(LIB_DIR)/mk/psql.mk
include $(LIB_DIR)/mk/flask.mk
