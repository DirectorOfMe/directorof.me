WEB_LOCATION ?= auth

LIB_DIR      ?= ../../lib
SHARE_DIR    ?= ../../share

default: build/asset-manifest.json

install: install-www

clean: clean-yarn

include $(LIB_DIR)/mk/js.mk
include $(LIB_DIR)/mk/web.mk
include ../../directorofme.conf
