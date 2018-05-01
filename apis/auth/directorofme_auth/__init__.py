'''
The `directorofme_auth` package, providing data models and REST API access to
authentication and authorization functionality for directorofme.

@author: Matthew Story <matt@directorof.me>
'''
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from directorofme.flask import versioned_api, app_for_api, JWTManager
from directorofme.authorization import groups, orm
from directorofme.flask import Model

__all__ = [ "app", "api", "config", "db", "exceptions", "jwt", "migrate", "resources", "models" ]

# ORDER MATTERS HERE
from .config import config
config = config()

###: TODO: this should be factored to a flask app ext or base model factory
Model.__tablename_prefix__ = config["name"]
Model.__scope__ = groups.Scope(display_name=config["name"])

from . import exceptions

db = SQLAlchemy(model_class=Model, query_class=orm.PermissionedQuery)

from . import models

api = versioned_api(config.get("api_name"))
jwt = JWTManager()

from . import resources

app = app_for_api(config["name"], config)

app.register_blueprint(api.blueprint)

db.init_app(app)
db.app = app

jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db, version_table=Model.version_table(), include_symbol=Model.include_symbol)
