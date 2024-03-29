### Must be provided
PSQL_DB         ?=
PSQL_USER       ?=
PSQL_PASSWORD   ?=
PSQL_HOST       ?=

PSQL_SHELL_USER ?= postgres
PSQL_VERSION    ?= 9.5
PSQL            ?= sudo -u "$(PSQL_SHELL_USER)" psql

.PHONY: postgresql
postgresql: .setup.postgresql.$(PSQL_DB).out

.setup.postgresql.$(PSQL_DB).out: .postgresql.apt.out
	{ \
		sudo -u "$(PSQL_SHELL_USER)" createdb "$(PSQL_DB)"; \
		echo "CREATE USER $(PSQL_USER) PASSWORD '$(PSQL_PASSWORD)';" | $(PSQL); \
		echo "GRANT ALL ON ALL TABLES IN SCHEMA public TO $(PSQL_USER);" | \
			$(PSQL) $(PSQL_DB); \
		echo "CREATE TABLE test (test INTEGER); \
			  INSERT INTO test VALUES (1); \
			  UPDATE test SET test = 2 WHERE test = 1; \
			  SELECT * FROM test; \
			  DELETE FROM test; \
			  DROP TABLE test;" | \
			 PGPASSWORD="$(PSQL_PASSWORD)" psql -h $(PSQL_HOST) $(PSQL_DB) $(PSQL_USER) \
			   || exit 1; \
	 } && touch $<

.postgresql.apt.out:
	sudo apt -y install postgresql-$(PSQL_VERSION) libpq-dev && touch $@

.PHONY: dropdb
dropdb: clean-postgresql.$(PSQL_DB).out
	sudo -u "$(PSQL_SHELL_USER)" dropdb "$(PSQL_DB)"

.PHONY: clean-postgresql
clean-postgresql: clean-postgresql.$(PSQL_DB).out
	rm -f .postgresql.apt.out

.PHONY: clean-postgresql.$(PSQL_DB).out
clean-postgresql.$(PSQL_DB).out:
	rm -f .setup.postgresql.$(PSQL_DB).out

.PHONY: db-shell
db-shell:
	PGPASSWORD="$(PSQL_PASSWORD)" psql -h "$(PSQL_HOST)" "$(PSQL_DB)" "$(PSQL_USER)"
