'''
The `directorofme_auth` package, providing data models and REST API access to
authentication and authorization functionality for directorofme.

@author: Matthew Story <matt@directorof.me>
'''
from flask_migrate import Migrate
from directorofme import flask_app, orm

__all__ = [ "app", "api", "config", "db", "exceptions", "jwt", "migrate", "resources", "models" ]

# ORDER MATTERS HERE
from .config import config
config = config()
orm.Model.__tablename_prefix__ = config["name"]

from . import exceptions
from .models import db
from . import models

from .resources import api, jwt
from . import resources

app = flask_app.api(config["name"], config)

app.register_blueprint(api.blueprint)

db.init_app(app)
db.app = app

jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db, version_table=orm.Model.version_table(), include_symbol=orm.Model.include_symbol)
