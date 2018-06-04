SHARE_DIR    ?= ../../share
TPL_DIR      ?= $(SHARE_DIR)/templates
BIN_DIR      ?= ../../bin

RENDER       ?= sh -c '\
					      $(BIN_DIR)/render_from_env $$RENDER_FLAGS $$1 $(TPL_DIR) \
				  	  ' render

SUBMAKE      ?= sh -c '\
	target=$$1; shift; \
	for dir in "$$@"; do sh -c " \
		cd $$dir || exit 1; \
		[ -f Makefile ] || exit 0; \
		make $$target; \
	" || exit $$?; done' submake

