import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from directorofme import flask_app
from directorofme.authorization import orm
from directorofme.authorization.groups import Scope
from directorofme.authorization.jwt import JWTManager

__all__ = [ "app", "db", "jwt", "migrate", "models" ]


app = flask_app.api(os.path.basename(os.path.dirname(__file__)), { "api_name": "event" })
orm.Model.__tablename_prefix__ = app.name
orm.Model.__scope__ = Scope(display_name=app.name)
orm.Model.load_groups = orm.Model.load_groups_from_flask_session

from . import models

db = SQLAlchemy(model_class=orm.Model)
db.init_app(app)
db.app = app

jwt = JWTManager()
jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db, version_table=orm.Model.version_table(), include_symbol=orm.Model.include_symbol)
