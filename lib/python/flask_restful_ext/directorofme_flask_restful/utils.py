'''
utils.py -- Helper functions and misc bits

@author: Matthew Story <matt@directorof.me>
'''

import functools

import flask
import flask_restful

__all__ = [ "resource_url", "versioned_api", "errors" ]

def resource_url(api, *args, **kwargs):
    '''Decorator for simplifying the add_resource interface:

       @resource_url(api, "/url/<foo>", endpoint="url")
       class Thing(Resource):
           def get(foo):
                return { "foo": "bar" }
    '''
    @functools.wraps(resource_url)
    def real_decorator(cls):
        api.add_resource(cls, *args, **kwargs)
        return cls

    return real_decorator

errors = {
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

    return flask_restful.Api(blueprint, errors=errors)
