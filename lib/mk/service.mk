DAEMONTOOLS_SRC      ?= http://untroubled.org/daemontools-encore/daemontools-encore-1.10.tar.gz
DAEMONTOOLS_CHECKSUM ?= a9b22e9eff5c690cd1c37e780d30cd78
CURL                 ?= curl

SERVICE_NAME         ?=
SERVICE_OWNER        ?=
SERVICE_OWNER_UID    ?=
SLASH_SERVICE_OWNER  ?= root
REAL_LOG_DIR         ?= /var/log/service

RUN_FILE_TPL         ?=
RUN_FILE_EXPORTS     ?=

LOG_RUN_FILE_TPL     ?= run.multilog
LOG_RUN_FILE_EXPORTS ?= DAEMON_USER="$(SERVICE_OWNER)"

#### INSTALL BITS
# TODO: check target to see if it exists
.PHONY: install-service
install-service: /service/.d /service-versions/.d service/run real-log-dir \
				service-owner /etc/systemd/service/svscanboot.service
	service_name=$(SERVICE_NAME)_`date +%Y%m%d%H%M%S`; \
		cp -rf service /service-versions/$$service_name && \
		chown -R $(SLASH_SERVICE_OWNER):$(SERVICE_OWNER) \
			     /service-versions/$$service_name && \
		ln -sf /service-versions/$$service_name /service-versions/$(SERVICE_NAME) && \
		mv /service-versions/$(SERVICE_NAME) /service/ && \
		find /service-versions/ -mindepth 1 -maxdepth 1 \
								-name '$(SERVICE_NAME)*' \
								-not -name "$$service_name" \
								-type d  | xargs -r -n1 -- sh -c ' \
									cd $$1; svc -dx . ./log; \
									cd /; rm -r $$1; \
								' cleanup

.PHONY: clean-service
clean-service:
	rm -rf service/

.PHONY: real-log-dir
real-log-dir: service-owner
	install -o $(SLASH_SERVICE_OWNER) -g $(SLASH_SERVICE_OWNER) -m 0755 \
			-d $(REAL_LOG_DIR)
	install -o $(SLASH_SERVICE_OWNER) -g $(SERVICE_OWNER) -m 0775 \
		    -d $(REAL_LOG_DIR)/$(SERVICE_NAME)

.PHONY: service-owner
service-owner:
	id $(SERVICE_OWNER) || useradd -u "$(SERVICE_OWNER_UID)" "$(SERVICE_OWNER)"

/service/.d: daemontools-check /service-versions/.d
	install -d -o $(SLASH_SERVICE_OWNER) -g $(SLASH_SERVICE_OWNER) -m 0755 /service
	touch $@

/service-versions/.d: daemontools-check
	install -o $(SLASH_SERVICE_OWNER) -g $(SLASH_SERVICE_OWNER) -m 0755 \
		    -d /service-versions
	touch $@

### BUILD BITS
service/run: service/log/run
	$(RUN_FILE_EXPORTS) $(RENDER) $(RUN_FILE_TPL) > $@.tmp
	install -m 0755 $@.tmp $@
	rm -f $@.tmp

service/log/run: service/log/main service-owner-check
	$(LOG_RUN_FILE_EXPORTS) $(RENDER) $(LOG_RUN_FILE_TPL) > $@.tmp
	install -m 0755 $@.tmp $@
	rm -f $@.tmp

service/log/main: service/log/.d service-name-check
	rm -f $@ && ln -sf $(REAL_LOG_DIR)/$(SERVICE_NAME) $@

service/log/.d: service/.d
	install -d service/log && touch $@

service/.d:
	install -d service && touch $@

.PHONY: service-name-check
service-name-check:
	[ "$(SERVICE_NAME)" ] || { echo "SERVICE_NAME must be set" >&2; exit 1; }

.PHONY: service-owner-check
service-owner-check:
	[ "$(SERVICE_OWNER)" ] || { echo "SERVICE_OWNER must be set" >&2; exit 1; }

.PHONY: daemontools-check
daemontools-check:
	which svscan > /dev/null 2>&1 || { \
		echo "please install daemontools before proceeding"; \
		exit 1; \
	}


### DAEMONTOOLS BITS
.PHONY: daemontools
daemontools: .daemontools/daemontools/.made
	cd .daemontools/daemontools && sudo make install

/etc/systemd/system/svscanboot.service: /lib/systemd/system/svscanboot.service
	sudo systemctl daemon-reload
	sudo systemctl enable svscanboot.service

/lib/systemd/system/svscanboot.service: $(SHARE_DIR)/systemd/svscanboot.service
	sudo install -o $(SLASH_SERVICE_OWNER) -g $(SLASH_SERVICE_OWNER) -m 0644 $< $@

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

include $(LIB_DIR)/mk/conf.mk
