import uuid
import flask
import flask_restful
import pytest

import marshmallow

from unittest import mock
from apispec import APISpec
from werkzeug.exceptions import NotFound, BadRequest

from directorofme.flask import api

class FixtureSchema(marshmallow.Schema):
    foo = marshmallow.fields.Integer(required=True)
    bar = marshmallow.fields.Integer()

@pytest.fixture
def flask_api(app):
    return flask_restful.Api(app)

def test__first_or_abort():
    query = mock.Mock()
    query.first.return_value = "TEST"

    assert api.first_or_abort(query) == "TEST", "non-None returns"

    query.first.return_value = None

    with pytest.raises(NotFound):
        api.first_or_abort(query)

def test__uuid_or_abort():
    uuid_ = uuid.uuid1()
    assert api.uuid_or_abort(str(uuid_)) == uuid_, "uuid-able string returns a UUID object"

    with pytest.raises(BadRequest):
        api.uuid_or_abort("abdddd")

def test__load_with_schema(request_context_with_session):
    loaded = mock.Mock()
    decorated = api.load_with_schema(FixtureSchema)(loaded)
    with mock.patch.object(flask.request, "get_json") as get_json_mock:
        get_json_mock.return_value = { "foo": 1, "bar": 2 }
        decorated()
        assert get_json_mock.called, "json_ mock called"
        loaded.assert_called_with({ "foo": 1, "bar": 2 })

    with pytest.raises(BadRequest), \
            mock.patch.object(flask.request, "get_json") as get_json_mock:
        get_json_mock.return_value = { "bar": 1 }
        decorated()

    decorated = api.load_with_schema(FixtureSchema, partial=True)(loaded)
    with mock.patch.object(flask.request, "get_json") as get_json_mock:
        get_json_mock.return_value = { "bar": 1 }
        decorated()
        assert get_json_mock.called, "json_ mock called"
        loaded.assert_called_with({ "bar": 1 })

def test__dump_with_schema():
    @api.dump_with_schema(FixtureSchema)
    def dumped():
        return { "foo": "1" }

    assert dumped() == { "foo": 1 }, "decorated function dumps"

    @api.dump_with_schema(FixtureSchema, many=True)
    def dumped_many(arg):
        return [{ "foo": "1" }, { "foo": arg }]

    assert dumped_many("2") == [{ "foo": 1 }, { "foo": 2 }], \
           "many kwarg is passed through to dump, passed arg is passed through to decorated function"

    @api.dump_with_schema(FixtureSchema)
    def not_found():
        pass

    with pytest.raises(NotFound):
        not_found()

    @api.dump_with_schema(FixtureSchema)
    def non_conforming():
        return { "foo": "abcdefgh" }

    with pytest.raises(BadRequest):
        non_conforming()

    @api.dump_with_schema(FixtureSchema)
    def return_tuple():
        return { "foo": 2 }, 404

    assert return_tuple() == ({ "foo": 2 }, 404), "tuple works"

def test__load_query_params(request_context_with_session):
    loaded_mock = mock.MagicMock()
    decorated = api.load_query_params(FixtureSchema)(loaded_mock)

    with pytest.raises(BadRequest):
        decorated()

    assert not loaded_mock.called, "inner function not called"
    with mock.patch.object(flask.request, "values", {"foo": 1}):
        decorated()
        loaded_mock.assert_called_with(foo=1)

def test__with_pagination_params(request_context_with_session):
    paginated_mock = mock.MagicMock()
    decorated = api.with_pagination_params()(paginated_mock)

    decorated()
    paginated_mock.assert_called_with(page=1, results_per_page=50)

    api.with_pagination_params(default_results_per_page=100)(paginated_mock)()
    paginated_mock.assert_called_with(page=1, results_per_page=100)

    with mock.patch.object(flask.request, "values", {"page": 2}):
        decorated()
        paginated_mock.assert_called_with(page=2, results_per_page=50)

    with mock.patch.object(flask.request, "values", {"results_per_page": 2}):
        decorated()
        paginated_mock.assert_called_with(page=1, results_per_page=2)

    with mock.patch.object(flask.request, "values", {"results_per_page": 100, "page": 2}):
        decorated()
        paginated_mock.assert_called_with(page=2, results_per_page=50)

    with mock.patch.object(flask.request, "values", {"results_per_page": 0, "page": 0}):
        decorated()
        paginated_mock.assert_called_with(page=1, results_per_page=1)

    with pytest.raises(BadRequest), \
            mock.patch.object(flask.request, "values", {"results_per_page": "abc", "page": 0}):
        decorated()

def test__with_cursor_params(request_context_with_session):
    cursor_mock = mock.MagicMock()
    decorated = api.with_cursor_params()(cursor_mock)

    decorated()
    cursor_mock.assert_called_with(results_per_page=50)

    uuid_ = uuid.uuid1()
    with mock.patch.object(flask.request, "values", { "max_id": str(uuid_) }):
        decorated()
        cursor_mock.assert_called_with(max_id=uuid_, results_per_page=50)

    with mock.patch.object(flask.request, "values", { "since_id": str(uuid_) }):
        decorated()
        cursor_mock.assert_called_with(since_id=uuid_, results_per_page=50)

    cursor_mock.reset_mock()
    with pytest.raises(BadRequest), \
            mock.patch.object(flask.request, "values", { "max_id": uuid_, "since_id": uuid_ }):
        decorated()
    assert not cursor_mock.called, "cursor mock not called"


class TestSpec:
    def test__name(self):
        assert api.Spec.name == "dom-apispec", "extension name is correct"

    def test__init__(self, app):
        spec = api.Spec(app, title="Test Spec", version="0.1.0")

        assert isinstance(spec.spec, APISpec), "spec instantiated correctly"
        assert spec.spec.to_dict()["info"]["title"] == "Test Spec", "kwarg successfully passed"
        assert app.extensions[spec.name] is spec, "spec installed to extensions"
        assert spec.app is app, "app saved as property"

        spec = api.Spec(title="Test Spec", version="0.0.1")
        assert "Error" in spec.to_dict()["definitions"], "added to spec"
        assert set(spec.to_dict()["parameters"].keys()) == \
               {"api_version", "slug", "uuid", "page", "results_per_page"}, "parameters set by __init__"

    def test__getattr__(self):
        spec = api.Spec(title="Test Spec", version="0.0.1")
        assert spec.to_dict == spec.spec.to_dict, "to_dict passes through"
        with pytest.raises(AttributeError):
            spec.no_this_does_not_exist_on_spec

    def test__init_app(self, app):
        paths = []
        current_app_mock = mock.Mock()

        class SubSpec(api.Spec):
            test_current_app = False

            def real_add_path(self, *args, **kwargs):
                if self.test_current_app:
                    current_app_mock()
                    assert flask.current_app._get_current_object() is app, "current app installed"
                paths.append([args, kwargs])

        spec = SubSpec(title="Sub", version="0.0.1")
        spec.add_path("a path", fake="argument")

        assert paths.pop() == [("a path",), { "fake": "argument" }], "subspec add path works"

        assert app.extensions.get(spec.name) is None, "not installed yet"
        spec.test_current_app = True
        spec.init_app(app)

        assert current_app_mock.called, "test for current app was executed"
        assert paths == [[("a path",), { "fake": "argument" }]], "init_app calls paths"
        assert app.extensions[spec.name] is spec, "installed to app"
        assert spec.app is None, "app is still None"

        paths = []
        spec.init_app(app)
        assert paths == [], "init_app a second time does not re-call add paths"

    def test__add_path(self, app):
        @app.route("/test")
        def test(request):
            pass

        spec = api.Spec(app, title="A", version="0.0.1")
        assert len(spec.paths) == 0, "paths empty to start"

        spec.add_path(view=test)
        assert len(spec.paths) == 1, "appended to paths"
        assert list(spec.to_dict()["paths"].keys()) == ["/test"], "path installed immediately"


    def test__real_add_path(self, app, flask_api):
        @app.route("/test")
        def test(request):
            pass

        @flask_api.resource("/test-2", endpoint="spec_api")
        class Foo(flask_restful.Resource):
            def get(self):
                pass

        spec = api.Spec(app, title="A", version="0.0.1")
        spec.real_add_path(view=test)
        assert list(spec.to_dict()["paths"].keys()) == ["/test"], "path installed immediately"
        assert spec.paths == [], "real_add_path does not mutate paths list"
        del app.extensions[api.Spec.name]

        spec = api.Spec(title="A", version="0.0.1")
        spec.real_add_path(view=test)

        assert list(spec.to_dict()["paths"].keys()) == [], "path not installed if no app present"
        with app.app_context():
            spec.real_add_path(view=test)
        assert list(spec.to_dict()["paths"].keys()) == [], "path not installed for uninitialized app"

        spec.init_app(app)
        with app.app_context():
            spec.real_add_path(view=test)
            assert list(spec.to_dict()["paths"].keys()) == ["/test"], "path installed if app is initialized"
            spec.real_add_path(view_class=Foo)

        assert list(spec.to_dict()["paths"]["/test-2"].keys()) == ["get"], "view class installed correctly"

    def test__register_resource(self, app, flask_api):
        spec = api.Spec(app, title="a", version="0.1")

        @spec.register_resource
        @flask_api.resource("/test-3", endpoint="spec_api")
        class Foo(flask_restful.Resource):
            def get(self):
                pass

        assert len(spec.paths) == 1, "registered to paths list"
        assert list(spec.to_dict()["paths"].keys()) == ["/test-3"], "added to spec"

    def test__register_schema(self, app):
        spec = api.Spec(app, title="a", version="0.1")

        @spec.register_schema("Schema")
        class Schema(marshmallow.Schema):
            pass

        assert "Schema" in spec.to_dict()["definitions"], "added to spec"
