LIB_DIR            ?= ../../lib
SHARE_DIR          ?= ../../share
FLASK_APP          ?= directorofme_auth:app

.PHONY: default
default: build-setup-py postgresql

.PHONY: clean
clean: clean-setup-py

.PHONY: install
install: default install-setup-py

include $(LIB_DIR)/mk/python.mk
include $(LIB_DIR)/mk/psql.mk
include $(LIB_DIR)/mk/flask.mk
