PIP       := pip3
PYTHON    := python3
SRC_DIR   := .
SETUP_PY  := setup.py
#TODO: this isn't working
PY_FILES  := $(find $(SRC_DIR) -type f -name '*.py')

.PHONY: build-setup-py
build-setup-py: build/.d

build/.d: $(SETUP_PY) $(PY_FILES)
	$(PYTHON) $(SETUP_PY) build && touch $@

.PHONY: install-setup-py
install-setup-py: build/.d
	$(PYTHON) $(SETUP_PY) install

.PHONY: clean-setup-py
clean-setup-py:
	rm -rf build/ dist/ *.egg-info/

.PHONY: clean.requirements.out
clean.requirements.out:
	rm -f .requirements.out

.requirements.out: requirements.txt
	$(PIP) install -r $< | tee $@
