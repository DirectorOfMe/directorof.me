APT             ?= sudo apt -y
PIP             ?= pip3
PYTHON          ?= python3
SRC_DIR         ?= .
LIB_DIR         ?= ../../lib
SHARE_DIR       ?= ../../share
TPL_DIR         ?= $(SHARE_DIR)/templates

SQLALCHEMY_DEPS  = psycopg2>=2.7.3,\
				   sqlalchemy>=1.2,\
                   sqlalchemy-utils>=0.32,
FLASK_PKG_DEPS   = $(SQLALCHEMY_DEPS),\
                   directorofme_flask_restful,\
                   flask==0.12.2,\
                   flask-restful==0.3.5,\
                   flask-jwt-extended[asymmetric_crypto]>=3.6,\
                   flask-sqlalchemy>=2.3.2,\
                   flask-migrate>=2.1.1,
PKG_DEPS        ?= ""
PKG_NAME        ?= ""
PKG_VERSION     ?= ""

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

build/.d: setup.py $(PY_FILES)
	$(PYTHON) setup.py build && touch $@

#TODO: automatically hook up py.test for projects
.PHONY: run-py-test
run-py-test: setup.py
	$(PYTHON) setup.py test

.PHONY: install-setup-py
install-setup-py: setup.py build/.d
	$(PYTHON) setup.py install

.PHONY: clean-setup-py
clean-setup-py:
	rm -rf build/ dist/ *.egg-info/ setup.cfg setup.py setup.cfg.tmp setup.py.tmp

.PHONY: clean.requirements.out
clean.requirements.out:
	rm -f .requirements.out

.requirements.out: requirements.txt pip
	$(PIP) install -r requirements.txt && touch $@

.PHONY: pip
pip: python3
	$(APT) install python3-pip

.PHONY: python3
python3:
	$(APT) install $(PYTHON)

include $(LIB_DIR)/mk/conf.mk
