import flask

from werkzeug.contrib.fixers import ProxyFix
from flask_migrate import Migrate

from directorofme import json

from . import config, db, api, jwt

__all__ = [ "app", "api", "db", "migrate" ]


app = flask.Flask(config["name"])
app.config.update(config["app"])
app.wsgi_app = ProxyFix(app.wsgi_app)
app.json_encoder = json.JSONEncoder
app.config["RESTFUL_JSON"] = { "cls": app.json_encoder }

with open(app.config["JWT_PUBLIC_KEY_FILE"]) as pub_key:
    app.config["JWT_PUBLIC_KEY"] = pub_key.read()

if app.config["IS_AUTH_SERVER"]:
    with open(app.config["JWT_PRIVATE_KEY_FILE"]) as private_key:
        app.config["JWT_PRIVATE_KEY"] = private_key.read()

app.register_blueprint(api.blueprint)

db.init_app(app)
db.app = app

jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db)
