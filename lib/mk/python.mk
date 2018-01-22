PIP       ?= pip3
PYTHON    ?= python3
SRC_DIR   ?= .
SETUP_PY  ?= setup.py
SHARE_DIR ?= ../../share
#TODO: this isn't working
PY_FILES  ?= $(find $(SRC_DIR) -type f -name '*.py')

.PHONY: build-setup-py
build-setup-py: build/.d setup.cfg

build/.d: $(SETUP_PY) $(PY_FILES)
	$(PYTHON) $(SETUP_PY) build && touch $@

#TODO: automatically hook up py.test for projects
.PHONY: test
test: setup.cfg
	$(PYTHON) $(SETUP_PY) test

.PHONY: install-setup-py
install-setup-py: build/.d
	$(PYTHON) $(SETUP_PY) install

.PHONY: clean-setup-py
clean-setup-py: clean-setup.cfg
	rm -rf build/ dist/ *.egg-info/

.PHONY: clean.requirements.out
clean.requirements.out:
	rm -f .requirements.out

.requirements.out: requirements.txt
	$(PIP) install -r $< | tee $@

setup.cfg: $(SHARE_DIR)/build_files/setup.cfg
	install -m 640 $< $@

.PHONY: clean-setup.cfg
clean-setup.cfg:
	rm -f setup.cfg
