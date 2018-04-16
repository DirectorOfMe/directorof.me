import os

import flask

from werkzeug.contrib.fixers import ProxyFix

from . import json
from .authorization.exceptions import MisconfiguredAuthError

__all__ = [ "app", "api", "db", "migrate" ]


def api(app_name, user_config):
    '''Construct a well-configured Flask application for building a DOM API'''
    config = default_config(app_name)
    app_config = config["app"]
    app_config.update(user_config.get("app", {}))

    config.update(user_config)
    config["app"] = app_config

    app = flask.Flask(config["name"])
    app.config.update(config["app"])
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.json_encoder = json.JSONEncoder
    app.config["RESTFUL_JSON"] = { "cls": app.json_encoder }

    try:
        with open(app.config["JWT_PUBLIC_KEY_FILE"]) as pub_key:
            app.config["JWT_PUBLIC_KEY"] = pub_key.read()
    except TypeError:
        raise MisconfiguredAuthError("JWT_PUBLIC_KEY_FILE must be set")
    except FileNotFoundError:
        raise MisconfiguredAuthError("JWT_PUBLIC_KEY_FILE not found: {}".format(app.config["JWT_PUBLIC_KEY_FILE"]))


    if app.config["IS_AUTH_SERVER"]:
        try:
            with open(app.config["JWT_PRIVATE_KEY_FILE"]) as private_key:
                app.config["JWT_PRIVATE_KEY"] = private_key.read()
        except TypeError:
            raise MisconfiguredAuthError("JWT_PRIVATE_KEY_FILE must be set")
        except FileNotFoundError:
            raise MisconfiguredAuthError("JWT_PRIVATE_KEY_FILE not found: "\
                                         "{}".format(app.config["JWT_PRIVATE_KEY_FILE"]))

    return app


def default_config(name=None):
    '''Standard config for DOM flask apps'''
    try:
        return {
            "name": name or os.environ["APP_NAME"],
            "app": {
                "DEBUG": os.environ.get("APP_DEBUG", False),
                "SQLALCHEMY_DATABASE_URI": os.environ.get("APP_DB_ENGINE"),
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                "PREFERRED_URL_SCHEME": "https",
                "SERVER_NAME": os.environ.get("SERVER_NAME"),
                "JWT_PUBLIC_KEY_FILE": os.environ.get("JWT_PUBLIC_KEY_FILE"),
                "JWT_PRIVATE_KEY_FILE": os.environ.get("JWT_PRIVATE_KEY_FILE"),
                "IS_AUTH_SERVER": os.environ.get("IS_AUTH_SERVER", False)
            },

            "api_name": os.environ.get("API_NAME"),
        }
    except KeyError:
        raise ValueError("Name must be provided as an argument or by environment "\
                         "variable `APP_CONFIG_NAME`")
