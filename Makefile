API_DIR             = ./apis
APP_DIR             = ./apps

APIS                = $(shell find $(API_DIR) -maxdepth 1 -mindepth 1 -type d)
APPS                = $(shell find $(APP_DIR) -maxdepth 1 -mindepth 1 -type d)

SUBMAKE             = sh -c 'target=$$1; shift; for dir in "$$@"; do cd $$dir && [ -f Makefile ] && { make $$target || exit $$?; } done' submake

# build targets
.PHONY: default
default: python apis apps

.PHONY: apis
apis:
	$(SUBMAKE) "" $(APIS)

.PHONY: apps
apps:
	$(SUBMAKE) "" $(APPS)

.PHONY: python
python: .requirements.txt

# install targets
.PHONY: install
install: install-apis install-apps

.PHONY: install-apis
install-apis:
	$(SUBMAKE) install $(APIS)

.PHONY: install-apps
install-apps:
	$(SUBMAKE) install $(APPS)

# clean targets
.PHONY: clean
clean: clean-python clean-apis clean-apps

.PHONY: clean-apps
clean-apps:
	$(SUBMAKE) clean $(APPS)

.PHONY: clean-apis
clean-apis:
	$(SUBMAKE) clean $(APIS)

.PHONY: clean-python
clean-python: clean.requirements.txt

include $(LIB_DIR)/mk/python.mk
