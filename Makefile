LIB_DIR             ?= ./lib
SHARE_DIR           ?= ./share
TPL_DIR             ?= $(SHARE_DIR)/templates
LIB_DIR             ?= ./lib
BIN_DIR             ?= ./bin
API_DIR             ?= ./apis
APP_DIR             ?= ./apps

PY_LIBS             ?= $(shell find $(LIB_DIR)/python -maxdepth 1 -mindepth 1 -type d)
APIS                ?= $(shell find $(API_DIR) -maxdepth 1 -mindepth 1 -type d)
APPS                ?= $(shell find $(APP_DIR) -maxdepth 1 -mindepth 1 -type d)

SUBMAKE             ?= sh -c 'target=$$1; shift; for dir in "$$@"; do sh -c "cd $$dir && [ -f Makefile ]  || exit 0; make $$target"; done' submake

# build targets
.PHONY: default
default: conf pip python py-libs apis apps error-pages ssl

.PHONY: all
all: default install upgrade-db

.PHONY: dev
dev: conf jwt_keys install-ssl
	$(SUBMAKE) dev $(APIS)

.PHONY: python
python: .requirements.out

.PHONY: py-libs
py-libs:
	$(SUBMAKE) "" $(PY_LIBS)

.PHONY: apis
apis:
	$(SUBMAKE) "" $(APIS)

.PHONY: apps
apps:
	$(SUBMAKE) "" $(APPS)

# install targets
.PHONY: install
install: daemontools install-py-libs install-apis install-apps configure-nginx

.PHONY: install-py-libs
install-py-libs:
	$(SUBMAKE) install $(PY_LIBS)

.PHONY: install-apis
install-apis:
	$(SUBMAKE) install $(APIS)

.PHONY: install-apps
install-apps:
	$(SUBMAKE) install $(APPS)

# clean targets
.PHONY: clean
clean: clean-py-libs clean-python clean-apis clean-apps clean-daemontools

.PHONY: clean-py-libs
clean-py-libs:
	$(SUBMAKE) clean $(PY_LIBS)

.PHONY: clean-apps
clean-apps:
	$(SUBMAKE) clean $(APPS)

.PHONY: clean-apis
clean-apis:
	$(SUBMAKE) clean $(APIS)

.PHONY: clean-python
clean-python: clean.requirements.out

.PHONY: upgrade-db
upgrade-db:
	$(SUBMAKE) $@ $(APIS)

.PHONY: conf
conf: directorofme.conf

directorofme.conf: $(TPL_DIR)/directorofme.conf
	RENDER_FLAGS="-p" $(RENDER) $@ > $@.tmp
	mv $@.tmp $@

include $(LIB_DIR)/mk/python.mk
include $(LIB_DIR)/mk/service.mk
include $(LIB_DIR)/mk/jwt.mk
include $(LIB_DIR)/mk/web.mk
include $(LIB_DIR)/mk/conf.mk
include directorofme.conf
