WEB_FILES_LOCATION ?= example

LIB_DIR      ?= ../../lib
SHARE_DIR    ?= ../../share

default: build/asset-manifest.json

install: install-www

clean: clean-yarn clean-package.json

include $(LIB_DIR)/mk/js.mk
include $(LIB_DIR)/mk/web.mk
include ../../directorofme.conf
