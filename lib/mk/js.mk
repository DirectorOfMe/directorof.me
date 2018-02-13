SHARE_DIR ?= ../../share

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
