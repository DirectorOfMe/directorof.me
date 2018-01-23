LIB_DIR             ?= ./lib
API_DIR             ?= ./apis
APP_DIR             ?= ./apps

PY_LIBS             ?= $(shell find $(LIB_DIR)/python -maxdepth 1 -mindepth 1 -type d)
APIS                ?= $(shell find $(API_DIR) -maxdepth 1 -mindepth 1 -type d)
APPS                ?= $(shell find $(APP_DIR) -maxdepth 1 -mindepth 1 -type d)

SUBMAKE             ?= sh -c 'target=$$1; shift; for dir in "$$@"; do sh -c "cd $$dir && [ -f Makefile ] && { make $$target || exit $$?; }"; done' submake

# build targets
.PHONY: default
default: | python py-libs apis apps postgresql

.PHONY: all
all: | default install upgrade-db

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
install: | install-py-libs install-apis install-apps

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
clean: clean-py-libs clean-python clean-apis clean-apps

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

# db bits
.PHONY: upgrade-db
upgrade-db:
	$(SUBMAKE) $@ $(APIS)

include $(LIB_DIR)/mk/python.mk
include $(LIB_DIR)/mk/psql.mk
