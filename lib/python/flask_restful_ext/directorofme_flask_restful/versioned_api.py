'''
versioned_api.py -- Shared functionality for versioned apis

@author: Matthew Story <matt@directorof.me>
'''
import flask
import flask_restful

__all__ = [ "versioned_api" ]

def store_version_in_a_global(api_version):
    flask.g.api_version = api_version

def get_version_from_a_global():
    try:
        return flask.g.api_version
    except AttributeError:
        return "-"

def versioned_api(api_name, version_setter=store_version_in_a_global, version_getter=get_version_from_a_global):
    blueprint = flask.Blueprint(api_name, __name__, url_prefix="/api/<api_version>/{}".format(api_name))

    @blueprint.url_value_preprocessor
    def version_processor(endpoint, values):
        version = values.pop("api_version")
        if version_setter is not None:
            version_setter(version)

    @blueprint.url_defaults
    def version_fetcher(endpoint, values):
        if "api_version" not in values:
            values["api_version"] = version_getter()

    return flask_restful.Api(blueprint)

