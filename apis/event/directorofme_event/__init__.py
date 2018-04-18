import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from directorofme import orm, flask_app
from directorofme.authorization.jwt import JWTManager

__all__ = [ "app", "db", "jwt", "migrate", "models" ]


app = flask_app.api(os.path.basename(os.path.dirname(__file__)), {})
orm.Model.__tablename_prefix__ = app.name

from . import models

db = SQLAlchemy(model_class=orm.Model)
db.init_app(app)

jwt = JWTManager()
jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db, version_table=orm.Model.version_table(), include_symbol=orm.Model.include_symbol)
