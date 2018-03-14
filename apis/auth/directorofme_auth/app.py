import flask
import flask_restful

from werkzeug.contrib.fixers import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from directorofme import json

from . import config, db, api

__all__ = [ "app", "api", "db", "migrate" ]


app = flask.Flask(config["name"])
app.config.update(config["app"])
app.wsgi_app = ProxyFix(app.wsgi_app)
app.json_encoder = json.JSONEncoder

app.register_blueprint(api.blueprint)

db.init_app(app)
### XXX: see issue #607 on flask-sqlalchemy
db.app = app

migrate = Migrate(app, db)
