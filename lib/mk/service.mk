SERVICE_OWNER        = root
DAEMONTOOLS_SRC      = http://untroubled.org/daemontools-encore/daemontools-encore-1.10.tar.gz
DAEMONTOOLS_CHECKSUM = a9b22e9eff5c690cd1c37e780d30cd78
CURL                 = curl


/service/.d:
	install -d -o $(SERVICE_OWNER) -g $(SERVICE_OWNER) -m 0755 /service
	touch $@

.PHONY: daemontools-check
daemontools-check:
	which svscan > /dev/null 2>&1 || { \
		echo "please install daemontools before proceeding"; \
		exit 1; \
	}

.PHONY: daemontools
daemontools: .daemontools/daemontools/.made
	cd .daemontools/daemontools && sudo make install

.daemontools/daemontools/.made: .daemontools/daemontools
	cd $< && make && touch .made

.daemontools/daemontools: .daemontools/daemontools.tar.gz
	cd .daemontools && \
	tar zxf daemontools.tar.gz \
	&& find . -maxdepth 1 -mindepth 1 -type d | xargs -n1 -I{} mv {} daemontools

.daemontools/daemontools.tar.gz: .daemontools/.d
	$(CURL) $(DAEMONTOOLS_SRC) > $@
	[ "$(DAEMONTOOLS_CHECKSUM)" = $$(md5sum $@ | awk '{ print $$1; }') ] || { \
		rm -f $@; echo "CHECKSUM MISMATCH" >&2; exit 2; \
	}

.daemontools/.d:
	install -d .daemontools && touch $@

.PHONY: clean-daemontools
clean-daemontools:
	rm -rf .daemontools/
