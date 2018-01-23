### NEEDS TO BE TEMPLATED INTO app.py
PSQL_DB         ?= dom
PSQL_USER       ?= dom
PSQL_PASS       ?= password
PSQL_HOST       ?= localhost

# XXX: This needs to move to ansible or similar
PSQL_SHELL_USER ?= postgres
PSQL_VERSION    ?= 9.5
PSQL            := sudo -u "$(PSQL_SHELL_USER)" psql

.PHONY: postgresql
postgresql: .setup.postgresql.out

.setup.postgresql.out: .postgresql.apt.out
	{ \
		sudo -u "$(PSQL_SHELL_USER)" createdb "$(PSQL_DB)"; \
		echo "CREATE USER $(PSQL_USER) PASSWORD '$(PSQL_PASS)';" | $(PSQL); \
		echo "GRANT ALL ON ALL TABLES IN SCHEMA public TO $(PSQL_USER);" | \
			$(PSQL) $(PSQL_DB); \
		echo "CREATE TABLE test (test INTEGER); \
			  INSERT INTO test VALUES (1); \
			  UPDATE test SET test = 2 WHERE test = 1; \
			  SELECT * FROM test; \
			  DELETE FROM test; \
			  DROP TABLE test;" | \
			 PGPASSWORD="$(PSQL_PASS)" psql -h $(PSQL_HOST) $(PSQL_DB) $(PSQL_USER) \
			   || exit 1; \
	 } | tee $<

.postgresql.apt.out:
	apt install postgresql-$(PSQL_VERSION) libpq-dev | tee $<
