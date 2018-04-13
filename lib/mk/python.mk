PIP              ?= sudo pip3
PYTHON           ?= python3
EXTRA_PYTHONPATH ?=
SRC_DIR          ?= .
LIB_DIR          ?= ../../lib
SHARE_DIR        ?= ../../share
TPL_DIR          ?= $(SHARE_DIR)/templates

SQLALCHEMY_DEPS ?= psycopg2>=2.7.3,\
				   sqlalchemy>=1.2,\
                   sqlalchemy-utils>=0.32,

PKG_DEPS        ?=
PKG_NAME        ?=
PKG_VERSION     ?=

#TODO: this isn't working
PY_FILES  ?= $(find $(SRC_DIR) -type f -name '*.py')

.PHONY: build-setup-py
build-setup-py: setup.py build/.d

setup.py: $(TPL_DIR)/setup.py setup.cfg
	PKG_VERSION="$(PKG_VERSION)" \
	PKG_NAME="$(PKG_NAME)" \
	PKG_DEPS="$(PKG_DEPS)" \
	    $(RENDER) $@ > $@.tmp
	mv $@.tmp $@

setup.cfg: $(TPL_DIR)/setup.cfg
	PKG_NAME="$(PKG_NAME)" \
	    $(RENDER) $@ > $@.tmp
	mv $@.tmp $@

build/.d: setup.py $(PY_FILES) check-python3
	$(PYTHON) setup.py build && $(PYTHON) setup.py bdist && touch $@

#TODO: automatically hook up py.test for projects
.PHONY: run-py-test
run-py-test: setup.py check-python3
	PYTHONPATH=".:$(EXTRA_PYTHONPATH):$$PYTHONPATH" $(PYTHON) setup.py test

.PHONY: install-setup-py
install-setup-py: setup.py build/.d check-python3
	sudo $(PYTHON) setup.py install

.PHONY: clean-setup-py
clean-setup-py:
	rm -rf build/ dist/ *.egg-info/ setup.cfg setup.py setup.cfg.tmp setup.py.tmp

.PHONY: clean.requirements.out
clean.requirements.out:
	rm -f .requirements.out .requirements.out.tmp

.requirements.out: requirements.txt check-pip
	$(PIP) install -r requirements.txt 2>&1 | tee $@.tmp
	mv $@.tmp $@

.PHONY: pip
pip: python3
	$(INSTALL) python3-pip

.PHONY: check-pip
check-pip:
	$(CHECK_PROG) $(PIP)

.PHONY: python3
python3:
	$(INSTALL) $(PYTHON)

.PHONY: check-python3
check-python3:
	$(CHECK_PROG) $(PYTHON)

include $(LIB_DIR)/mk/conf.mk
include $(LIB_DIR)/mk/shared.mk
