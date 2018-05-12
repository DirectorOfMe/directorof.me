WEB_FILES_LOCATION  ?=
WEB_FILES_SRC       ?= build/
LIB_DIR             ?= ../../lib
SHARE_DIR           ?= ../../share
TPL_DIR             ?= $(SHARE_DIR)/templates .

PACKAGE_JSON_ENV = $(WEB_LOCATION)

### Targets for JS Packages
build/asset-manifest.json: yarn.lock
	yarn build

yarn.lock: package.json
	yarn

clean-package.json:
	rm -f package.json

package.json: package.json.tpl
	$(PACKAGE_JSON_ENV) $(RENDER) ./$< > $@.tmp
	mv $@.tmp $@

clean-yarn:
	rm -rf yarn.lock build/

### Setting Up Yarn
.PHONY: yarn
yarn: yarn-repo
	sudo apt-get update
	$(APT) install yarn

.PHONY: yarn-repo
yarn-repo: $(SHARE_DIR)/js/yarn.apt.key $(SHARE_DIR)/js/node.apt.key \
	   	   /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/node.list
	sudo apt-key add $(SHARE_DIR)/js/yarn.apt.key
	sudo apt-key add $(SHARE_DIR)/js/node.apt.key

/etc/apt/sources.list.d/%.list: $(SHARE_DIR)/js/%.apt.list
	sudo install -o root -g root -m 0644 $< $@

include $(LIB_DIR)/mk/shared.mk
include $(LIB_DIR)/mk/conf.mk
