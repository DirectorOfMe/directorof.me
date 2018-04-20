import json

import flask
import pytest

from unittest import mock
from flask_restful import Resource

from directorofme.testing import dict_from_response
from directorofme.authorization.exceptions import PermissionDeniedError
from directorofme_flask_restful import resource_url, versioned_api

def test__resource_url(app, api):
    @resource_url(api, "/endpoint", endpoint="endpoint")
    class Endpoint(Resource):
        def get(self):
            return { "hello": "world" }


    with app.test_client() as client:
        resp = client.get("/endpoint")
        assert json.loads(resp.get_data().decode("utf-8")) == { "hello": "world" }

@pytest.fixture
def v_api(app):
    api = versioned_api("test")
    app.register_blueprint(api.blueprint)
    return api

class TestVersionedApi:
    def test__default_behavior(self, app, v_api):
        @resource_url(v_api, "/foo", endpoint="foo")
        class Foo(Resource):
            def get(self):
                assert int(flask.g.api_version) == 2, "version was set correctly"
                return { "url": v_api.url_for(Foo) }


        with app.test_client() as client:
            resp = client.get("/api/2/test/foo")
            assert dict_from_response(resp) == { "url": "/api/2/test/foo" }, "url fetched correctly"

    def test__no_api_version(self, app, v_api):
        @resource_url(v_api, "/bar", endpoint="bar")
        class Bar(Resource):
            def get(self):
                del flask.g.api_version
                return { "url": v_api.url_for(Bar) }

        with app.test_client() as client:
            resp = client.get("/api/2/test/bar")
            assert dict_from_response(resp) == { "url": "/api/-/test/bar" }, "url fetched correctly"


    def test__custom_setters_and_getters(self, app, api):
        setter = mock.MagicMock()
        getter = mock.MagicMock()
        getter.return_value = "custom"

        v_api = versioned_api("test", version_setter=setter, version_getter=getter)
        app.register_blueprint(v_api.blueprint)

        @resource_url(v_api, "/baz", endpoint="baz")
        class Baz(Resource):
            def get(self):
                return { "url": v_api.url_for(Baz) }

        with app.test_client() as client:
            resp = client.get("api/2/test/baz")
            assert setter.called_with("2"), "setter called"
            assert getter.called, "getter was called"

            assert dict_from_response(resp) == { "url": "/api/custom/test/baz" }, "url used custom getter"


    def test__errors_handled(self, app, api):
        v_api = versioned_api("test")
        app.register_blueprint(v_api.blueprint)

        @resource_url(v_api, "/error", endpoint="error")
        class Error(Resource):
            def get(self):
                raise PermissionDeniedError()

        with app.test_client() as client:
            resp = client.get("api/2/test/error")
            assert resp.status_code == 401, "Permission denied returns a 401"
