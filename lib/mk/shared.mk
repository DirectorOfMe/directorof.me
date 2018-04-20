APT        ?= sudo apt -y
INSTALL    ?= $(APT) install

CHECK_PROG ?= sh -c 'which $$1 || { echo "$$1 not installed"; exit $$?; }' check
ADD_USER   ?= sh -c 'name=$$1; shift; \
				     uid=$$1; shift; \
					 id "$$name" > /dev/null || useradd -u "$$uid" "$$name"; \
					 while [ $$\# -gt 0 ]; do \
						group=$$1; shift; \
						sudo adduser $$name $$group; \
					 done' add
