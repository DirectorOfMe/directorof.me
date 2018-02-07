DirectorOf.Me
=============

We help people and teams do their best work.

How?
----

We help drive understanding and improvements to the quality and delivery of
work through the analysis of readily-available data and it's educated use by
people and teams.

Build
-----

To get started:

```
./install
```

If you are in a development environment, this will install all your
dependencies as well as setting up a database to be used by the various
DirectorOf.Me services that *will* run (NB: they do not run automatically
yet).

To jump into your new db and take a look around (in dev):

```
PGPASSWORD=password psql -h localhost dom dom
```

Once greeted with the prompt you can inspect the schema with `\d` and tables
with `\d+ <name>`.


Writing an API
--------------

The current best-practice for writing a REST API is to use Flask with
Flask-Restful. For an example of how to best build this, check out the
[apis/auth](/apis/auth) service. For model storage we use PostgreSQL in
development and production, and alembic for migrations (by way of
Flask-Migrate).

Dependency and installation management of packages is handled using `setuptools`,
so your API directory should have a `setup.py` in it that specifies the name
of the package you're writing, the version and any dependencies. For an
example of this see `apis/auth/setup.py`.

##### Configuring the DB Connection

By convention we configure the DB using environment variables. Specifically
the variable `APP_DB_ENGINE`. Various `make` commands in the build process
make use of this convention, so be sure to keep `lib/mk/psql.mk` up-to-date.
(NB: This needs to change to be in a build config separate from checked-in
code).

To make sure this is always correctly configured, please use the `make` helper
commands (`make shell`, `make migrate`, `make upgrade-db`) and always start
services using the run-file included in the API directory `service/run` rather
than starting things by hand.

##### DB Migrations

After you write your DB models you'll want to migrate them. This is easily done with:

```
make migrate
```

Which will create a DB migration in the `migrations` directory. If you use
`sqlalchemy_utils` types, you'll need to massage the generated files before
running them. Go in and swap out any `sqlalchemy_utils.types.UUIDField` calls
with `sa.dialects.postgresql.UUID` and any `sqlalchemy_utils.types.JSONType`
with `sa.dialects.postgresql.JSON` for now. See
[Issue 106](https://github.com/kvesteri/sqlalchemy-utils/issues/106) for more.

##### Running your API

We use `daemontools-encore` to daemonize our services. NB: finish this
implementation and then document it here.
