import os

import flask
import flask_restful

from werkzeug.contrib.fixers import ProxyFix

from . import JSONEncoder
from ..authorization.exceptions import MisconfiguredAuthError

__all__ = [ "app_for_api", "default_config", "rest_errors_map", "versioned_api" ]


def app_for_api(app_name, user_config):
    '''Construct a well-configured Flask application for building a DOM API'''
    config = default_config(app_name)
    app_config = config["app"]
    app_config.update(user_config.get("app", {}))

    config.update(user_config)
    config["app"] = app_config

    app = flask.Flask(config["name"])
    app.config.update(config["app"])
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.json_encoder = JSONEncoder
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


rest_errors_map = {
    'PermissionDeniedError': {
        'message': "You do not have permission to perform this action",
        'status': 401,
    }
}

def store_version_in_a_global(api_version):
    '''Default version storage method'''
    flask.g.api_version = api_version

def get_version_from_a_global():
    '''Default version retrieval method'''
    try:
        return flask.g.api_version
    except AttributeError:
        return "-"

def versioned_api(api_name, version_setter=store_version_in_a_global,
                  version_getter=get_version_from_a_global):
    '''Create a blueprint for a Flask-Restful API which respects a versioning
       convention. Pre-processors can store this information somewhere, the
       default is to store it to the `flask.g` variable for use by other
       methods.'''
    blueprint = flask.Blueprint(api_name, __name__, url_prefix="/api/<api_version>/{}".format(api_name))

    @blueprint.url_value_preprocessor
    def version_processor(endpoint, values):
        '''Process the version variable so every end-point doesn't have to deal with it'''
        version = values.pop("api_version")
        if version_setter is not None:
            version_setter(version)

    @blueprint.url_defaults
    def version_fetcher(endpoint, values):
        '''Fetch the version when building a URL so we don't need to provide it manually'''
        if "api_version" not in values:
            values["api_version"] = version_getter()

    return flask_restful.Api(blueprint, errors=rest_errors_map)
