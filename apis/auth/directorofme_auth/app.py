import os

import flask
import flask_restful
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from directorofme import orm

__all__ = [ "app", "api", "db", "migrate" ]

config = {
    "name": os.environ.get(
        "APP_CONFIG_NAME",
        os.path.basename(os.path.dirname(__file__))
    ),
    "app": {
        "DEBUG": os.environ.get("APP_DEBUG", False),
        "SQLALCHEMY_DATABASE_URI": os.environ.get("APP_DB_ENGINE", None),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    }
}

app = flask.Flask(config["name"])
app.config.update(config["app"])
api = flask_restful.Api(app)
db = SQLAlchemy(app, model_class=orm.Model)
migrate = Migrate(app, db)
