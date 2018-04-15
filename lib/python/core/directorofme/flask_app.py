import os

import flask

from werkzeug.contrib.fixers import ProxyFix

from . import json

__all__ = [ "app", "api", "db", "migrate" ]


def api(user_config):
    config = default_config()
    config.update(user_config)

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

    return app


def default_config():
    return {
        "name": os.environ.get(
            "APP_CONFIG_NAME",
            os.path.basename(os.path.dirname(__file__))
        ),
        "app": {
            "DEBUG": os.environ.get("APP_DEBUG", False),
            "SQLALCHEMY_DATABASE_URI": os.environ.get("APP_DB_ENGINE", None),
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "PREFERRED_URL_SCHEME": "https",
            "SERVER_NAME": os.environ.get("SERVER_NAME"),
            "JWT_PUBLIC_KEY_FILE": os.environ.get("JWT_PUBLIC_KEY_FILE"),
            "JWT_PRIVATE_KEY_FILE": os.environ.get("JWT_PRIVATE_KEY_FILE"),
            "IS_AUTH_SERVER": True
        },

        "API_NAME": os.environ.get("API_NAME"),
    }
