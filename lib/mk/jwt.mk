SHARE_DIR ?= ../../share
KEY_DIR   ?= jwt_keys

$(SHARE_DIR)/$(KEY_DIR)/.d:
	install -d -m 700 $(SHARE_DIR)/$(KEY_DIR)
	touch $@

$(SHARE_DIR)/$(KEY_DIR)/jwt_ec512.pem: $(SHARE_DIR)/$(KEY_DIR)/.d
	[ -f $@ ] || openssl ecparam -genkey -name secp521r1 -noout -out $@

$(SHARE_DIR)/$(KEY_DIR)/jwt_ec512_pub.pem: $(SHARE_DIR)/$(KEY_DIR)/jwt_ec512.pem
	[ -f $@ ] || openssl ec -in $< -outform PEM -pubout -out $@


.PHONY: jwt_keys
jwt_keys: $(SHARE_DIR)/$(KEY_DIR)/jwt_ec512_pub.pem
