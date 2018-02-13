LIB_DIR         ?= ../
SHARE_DIR       ?= ../../share/

# these must be provided
WEB_USER        ?=
WEB_UID         ?=
WEB_SERVER_NAME ?=
WEB_CONF_DIR    ?=
WEB_LOG_DIR     ?=
WEB_FILES_DIR   ?=
WEB_USE_SSL     ?=

RENDER_EXPORTS  ?= WEB_SERVER_NAME="$(WEB_SERVER_NAME)" \
				   WEB_USER="$(WEB_USER)" \
				   WEB_CONF_DIR="$(WEB_CONF_DIR)" \
				   WEB_LOG_DIR="$(WEB_LOG_DIR)" \
				   WEB_FILES_DIR="$(WEB_FILES_DIR)" \
				   WEB_USE_SSL="$(WEB_USE_SSL)"

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

/etc/nginx/sites-enabled/.d: /etc/nginx/.d
	sudo install -o root -g root -m 0755 -d /etc/nginx/sites-enabled && sudo touch $@

/etc/nginx/.d:
	sudo install -o root -g root -m 0755 -d /etc/nginx && sudo touch $@

/var/log/nginx/.d:
	sudo install -o root -g root -m 0755 -d /var/log/nginx && sudo touch $@

/var/www/errors/%.html: $(SHARE_DIR)/web/errors/%.html /var/www/errors/.d web-user
	sudo install -o root -g $(WEB_USER) -m 0644 $< $@

/var/www/errors/.d: /var/www/.d web-user
	sudo install -o root -g $(WEB_USER) -m 0755 -d /var/www/errors && sudo touch $@

/var/www/.d: web-user
	sudo install -o root -g $(WEB_USER) -m 0755 -d /var/www/ && sudo touch $@

.PHONY: install-error-pages
install-error-pages: /var/www/errors/404.html /var/www/errors/500.html

/etc/nginx/sites-enabled/default.conf: /etc/nginx/sites-enabled/.d \
									   install-error-pages \
									   $(SHARE_DIR)/templates/nginx/default.conf
	$(RENDER_EXPORTS) $(RENDER) nginx/default.conf | \
		sudo sh -c 'cat > $@.tmp || rm $@.tmp'
	sudo install -o root -g root -m 0644 $@.tmp $@; sudo rm -f $@.tmp

.PHONY: web-user
web-user:
	$(ADD_USER) $(WEB_USER) $(WEB_UID)

.PHONY: check-nginx
check-nginx:
	$(CHECK_PROG) nginx

# TODO: after we get this working, remove all the default crap
.PHONY: nginx
nginx:
	which nginx || { \
		$(APT) install nginx nginx-extras && \
		sudo service nginx stop && \
		sudo rm -rf /etc/nginx/ /var/www/ && \
		sudo rm -rf /var/log/nginx/; \
	}

include $(LIB_DIR)/mk/shared.mk
include $(LIB_DIR)/mk/conf.mk
