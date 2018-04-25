import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from directorofme import flask_app
from directorofme.authorization.orm import PermissionedQuery
from directorofme.authorization.groups import Scope
from directorofme.authorization.flask import JWTManager, Model

__all__ = [ "app", "db", "jwt", "migrate", "models" ]


app = flask_app.api(os.path.basename(os.path.dirname(__file__)), { "api_name": "event" })

Model.__tablename_prefix__ = app.name
Model.__scope__ = Scope(display_name=app.name)

from . import models

db = SQLAlchemy(model_class=Model, query_class=PermissionedQuery)
db.init_app(app)
db.app = app

jwt = JWTManager()
jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db, version_table=Model.version_table(), include_symbol=Model.include_symbol)
