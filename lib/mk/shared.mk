APT        ?= sudo apt -y
INSTALL    ?= $(APT) install

CHECK_PROG ?= sh -c 'which $$1 || { echo "$$1 not installed"; exit $$?; }' check
ADD_USER   ?= sh -c 'name=$$1; shift; \
				     uid=$$2; shift; \
					 id $$1 > /dev/null || useradd -u "$$2" "$$1"; \
					 while [ $$\# -gt 0 ]; do \
						group=$$1; shift; \
						adduser $$name $$group; \
					 done' add
