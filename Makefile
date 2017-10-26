API_DIR = ./apis
APP_DIR = ./apps

APIS                = $(shell find $(API_DIR) -maxdepth 1 -mindepth 1 -type d)
APPS                = $(shell find $(APP_DIR) -maxdepth 1 -mindepth 1 -type d)

SUBMAKE             = sh -c 'target=$$1; shift; for dir in "$$@"; do cd $$dir && [ -f Makefile ] && make $$target; done' submake

.PHONY: default
default: apis apps

.PHONY: apis
apis:
	$(SUBMAKE) "" $(APIS)

.PHONY: apps
apps:
	$(SUBMAKE) "" $(APPS)

.PHONY: clean
clean: clean-apis clean-apps

.PHONY: clean-apps
clean-apps:
	$(SUBMAKE) clean $(APPS)

.PHONY: clean-apis
clean-apis:
	$(SUBMAKE) clean $(APIS)
