APT        ?= sudo apt -y
INSTALL    ?= $(APT) install

CHECK_PROG ?= sh -c 'which $$1 || { echo "$$1 not installed; aborting"; exit $$?; }'
