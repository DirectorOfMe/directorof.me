APT        ?= sudo apt -y
INSTALL    ?= $(APT) install

CHECK_PROG ?= sh -c 'which $$1 || { echo "$$1 not installed"; exit $$?; }' check
ADD_USER   ?= sh -c 'id $$1 > /dev/null || useradd -u "$$2" "$$1"' add
