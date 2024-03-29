LIB_DIR           ?= ../
SHARE_DIR         ?= ../../share/

# these must be provided
WEB_USER          ?=
WEB_UID           ?=
WEB_SERVER_NAME   ?=
WEB_CONF_DIR      ?=
WEB_LOG_DIR       ?=
WEB_FILES_DIR     ?=
WEB_USE_SSL       ?=
WEB_SERVER_PORT   ?=
WEB_SERVER_SSL_PORT   ?=

PROXY_NAME        ?=
PROXY_HOST        ?=
PROXY_PORT        ?=
WEB_LOCATION      ?=
WEB_FILES_SRC     ?=

SSL_COUNTRY       ?=
SSL_STATE         ?=
SSL_LOCATION      ?=
SSL_ORGANIZATION  ?=
SSL_COMMON_NAME   ?=
SSL_DH_PARAM_LEN  ?=

INSTALL_WEB_PAGES ?= sh -c '\
	dir_name=/var/www-versions/$$2_`date +%Y%m%d%H%M%S`; \
		cp -rf $$1 $$dir_name && \
		chown -R $(WEB_USER):$(WEB_USER) $$dir_name && \
		find $$dir_name -type f | xargs -r -- chmod 0644 && \
		find $$dir_name -type d | xargs -r -- chmod 0755 && \
		ln -sf $$dir_name /var/www-versions/$$2 && \
		mv /var/www-versions/$$2 /var/www/ && \
		find /var/www-versions/ -mindepth 1 -maxdepth 1 \
							    -name "$$2*" -not -name "$${dir_name\#\#*/}" \
								-type d | xargs -r -- rm -rf;' install-web-pages

RENDER_EXPORTS    ?= WEB_SERVER_NAME="$(WEB_SERVER_NAME)" \
				     WEB_USER="$(WEB_USER)" \
				     WEB_CONF_DIR="$(WEB_CONF_DIR)" \
				     WEB_LOG_DIR="$(WEB_LOG_DIR)" \
				     WEB_FILES_DIR="$(WEB_FILES_DIR)" \
				     WEB_USE_SSL="$(WEB_USE_SSL)" \
				     WEB_SERVER_PORT="$(WEB_SERVER_PORT)" \
				     WEB_SERVER_SSL_PORT="$(WEB_SERVER_SSL_PORT)" \

PROXY_EXPORTS     ?= PROXY_NAME="$(PROXY_NAME)" \
				     PROXY_HOST="$(PROXY_HOST)" \
				     PROXY_PORT="$(PROXY_PORT)" \
				     WEB_LOCATION="$(WEB_LOCATION)"

#### Targets used by apps and apis
.PHONY: install-proxy-conf
install-proxy.conf: /etc/nginx/locations/.d proxy.conf
	install -o root -g root -m 0644 proxy.conf \
		/etc/nginx/locations/$(PROXY_NAME).conf
	sudo service nginx restart

proxy.conf: $(SHARE_DIR)/templates/nginx/locations/proxy.conf
	$(PROXY_EXPORTS) $(RENDER) nginx/locations/proxy.conf > $@.tmp && mv $@.tmp $@

.PHONY: install-www
install-www:
	$(INSTALL_WEB_PAGES) $(WEB_FILES_SRC) $(WEB_FILES_LOCATION)

#### Targets used by main installer to configure nginx itself
.PHONY: clean-proxy.conf
clean-proxy.conf:
	rm -f proxy.conf

.PHONY: configure-nginx
configure-nginx: nginx \
				 /etc/nginx/sites-enabled/default.conf \
				 /etc/nginx/nginx.conf
	sudo service nginx restart

/etc/nginx/nginx.conf: $(SHARE_DIR)/templates/nginx/nginx.conf \
					   /etc/nginx/includes/mime.types \
				       /var/log/nginx/.d \
				   	   /etc/nginx/includes/proxy_params.conf /etc/nginx/.d
	$(RENDER_EXPORTS) $(RENDER) nginx/nginx.conf | \
		sudo sh -c 'cat > $@.tmp || rm $@.tmp'
	sudo install -o root -g root -m 0644 $@.tmp $@; sudo rm -f $@.tmp

/etc/nginx/includes/mime.types: $(SHARE_DIR)/templates/nginx/includes/mime.types \
								/etc/nginx/includes/.d
	$(RENDER_EXPORTS) $(RENDER) nginx/includes/mime.types | \
		sudo sh -c 'cat > $@.tmp || rm $@.tmp'
	sudo install -o root -g root -m 0644 $@.tmp $@; sudo rm -f $@.tmp

/etc/nginx/includes/proxy_params.conf: \
		$(SHARE_DIR)/templates/nginx/includes/proxy_params.conf \
		/etc/nginx/includes/.d
	$(RENDER_EXPORTS) $(RENDER) nginx/includes/proxy_params.conf | \
		sudo sh -c 'cat > $@.tmp || sudo rm $@.tmp'
	sudo install -o root -g root -m 0644 $@.tmp $@; sudo rm -f $@.tmp

/etc/nginx/includes/.d:
	sudo install -o root -g root -m 0755 -d /etc/nginx/includes && sudo touch $@

/etc/nginx/locations/.d:
	sudo install -o root -g root -m 0755 -d /etc/nginx/locations && sudo touch $@

/etc/nginx/sites-enabled/.d: /etc/nginx/.d
	sudo install -o root -g root -m 0755 -d /etc/nginx/sites-enabled && sudo touch $@

.PHONY: install-ssl
install-ssl: /etc/nginx/ssl/nginx.crt \
			 /etc/nginx/ssl/nginx.key \
			 /etc/nginx/ssl/dhparam.pem

/etc/nginx/ssl/%: $(SHARE_DIR)/ssl/% /etc/nginx/ssl/.d
	sudo install -o root -g root -m 0600 $< $@

/etc/nginx/ssl/.d:
	sudo install -o root -g root -m 0700 -d /etc/nginx/ssl && sudo touch $@

# SSL settings
.PHONY: ssl
ssl: $(SHARE_DIR)/ssl/dhparam.pem
$(SHARE_DIR)/ssl/dhparam.pem: $(SHARE_DIR)/ssl/nginx.key
	openssl dhparam -out $@ $(SSL_DH_PARAM_LEN)

$(SHARE_DIR)/ssl/nginx.key: $(SHARE_DIR)/ssl/nginx.crt
$(SHARE_DIR)/ssl/nginx.crt: $(SHARE_DIR)/ssl/.d
	openssl req -x509 -nodes -sha256 -days 365 -newkey rsa:2048 \
		 -keyout $(SHARE_DIR)/ssl/nginx.key \
		 -out $@ -subj "/C=$(SSL_COUNTRY)/ST=$(SSL_STATE)/L=$(SSL_LOCATION)/O=$(SSL_ORGANIZATION)/CN=$(SSL_COMMON_NAME)"

$(SHARE_DIR)/ssl/.d:
	install -m 0700 -d $(SHARE_DIR)/ssl && touch $@

/etc/nginx/.d:
	sudo install -o root -g root -m 0755 -d /etc/nginx && sudo touch $@

/var/log/nginx/.d:
	sudo install -o root -g root -m 0755 -d /var/log/nginx && sudo touch $@

/etc/nginx/sites-enabled/default.conf: /etc/nginx/sites-enabled/.d \
									   install-error-pages install-ssl \
									   $(SHARE_DIR)/templates/nginx/default.conf
	$(RENDER_EXPORTS) $(RENDER) nginx/default.conf | \
		sudo sh -c 'cat > $@.tmp || rm $@.tmp'
	sudo install -o root -g root -m 0644 $@.tmp $@; sudo rm -f $@.tmp

.PHONY: install-error-pages
install-error-pages: error-pages web-user /var/www-versions/.d /var/www/.d
	$(INSTALL_WEB_PAGES) www-errors errors

.PHONY: error-pages
error-pages: www-errors/404.html www-errors/500.html

www-errors/%.html: $(SHARE_DIR)/web/errors/%.html www-errors/.d
	install -m 0644 $< $@

www-errors/.d:
	mkdir -p www-errors && touch $@

/var/www-versions/.d:
	sudo install -o root -g $(WEB_USER) -m 0755 -d /var/www-versions/ && sudo touch $@

/var/www/.d: web-user
	sudo install -o root -g $(WEB_USER) -m 0755 -d /var/www/ && sudo touch $@

.PHONY: web-user
web-user:
	$(ADD_USER) $(WEB_USER) $(WEB_UID)

.PHONY: check-nginx
check-nginx:
	$(CHECK_PROG) nginx

# TODO: after we get this working, remove all the default crap
.PHONY: nginx
nginx:
	sudo which nginx || { \
		$(APT) install nginx nginx-extras && \
		sudo service nginx stop && \
		sudo rm -rf /etc/nginx/ /var/www/ && \
		sudo rm -rf /var/log/nginx/; \
	}

include $(LIB_DIR)/mk/shared.mk
include $(LIB_DIR)/mk/conf.mk
