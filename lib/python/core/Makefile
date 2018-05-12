LIB_DIR     ?= ../../
SHARE_DIR   ?= ../../../share
TPL_DIR     ?= $(SHARE_DIR)/templates
BIN_DIR     ?= ../../../bin

PKG_NAME    ?= directorofme
PKG_VERSION ?= 0.1
PKG_DEPS    ?= $(FLASK_PKG_DEPS)

.PHONY: default
default: build-setup-py

.PHONY: clean
clean: clean-setup-py

.PHONY: install
install: install-setup-py

.PHONY: test
test: run-py-test

include $(LIB_DIR)/mk/flask.mk
