import uuid
import functools
import flask
import marshmallow

from flask_restful import abort

from collections import namedtuple
from apispec import APISpec

__all__ = [ "first_or_abort", "uuid_or_abort", "load_with_schema", "dump_with_schema",
            "with_pagination_params", "with_cursor_params", "Spec" ]

def _abort_if_errors(result):
    if result.errors:
        messages = ["{}: {}".format(k,v) for k,v in result.errors.items()]
        abort(400, message="Validation failed: {}".format(", ".join(messages)))
    return result.data

def first_or_abort(query):
    obj = query.first()
    if obj is None:
        abort(404, message="Could not find object")
    return obj

def uuid_or_abort(uuid_):
    try:
        return uuid.UUID(uuid_)
    except ValueError:
        abort(400, message="Cannot convert to UUID: {}".format(uuid_))

def load_with_schema(Schema, **load_kwargs):
    """
    Validate request body (JSON) and load it into a dictionary
    """
    @functools.wraps(load_with_schema)
    def inner(fn):
        @functools.wraps(fn)
        def inner_inner(*args, **kwargs):
            data = _abort_if_errors(Schema().load(flask.request.get_json() or {}, **load_kwargs))
            return fn(*args, data, **kwargs)

        return inner_inner

    return inner

def dump_with_schema(Schema, **dump_kwargs):
    """
    Validate output and encode to a JSON serializable format via a marshmellow.Schema object.
    """
    @functools.wraps(dump_with_schema)
    def inner(fn):
        @functools.wraps(fn)
        def inner_inner(*args, **kwargs):
            obj = fn(*args, **kwargs)
            response_tuple = None

            if isinstance(obj, tuple):
                response_tuple = obj[1:]
                obj = obj[0]

            if obj is None:
                abort(404, message="No object found")

            obj = _abort_if_errors(Schema().dump(obj, **dump_kwargs))
            if response_tuple is None:
                return obj
            return (obj,) + response_tuple

        return inner_inner

    return inner


def load_query_params(Schema):
    """
    Load query params from a defined query string.
    """
    @functools.wraps(load_query_params)
    def inner(fn):
        @functools.wraps(fn)
        def inner_inner(*args, **kwargs):
            kwargs.update(_abort_if_errors(Schema().load(flask.request.values)))
            return fn(*args, **kwargs)

        return inner_inner

    return inner


def with_pagination_params(default_results_per_page=50):
    """
    Validate and pass the standard pagination parameters for collections endpoints into a decorated
    MethodView method.
    """
    class PaginationParams(marshmallow.Schema):
        page = marshmallow.fields.Integer()
        results_per_page = marshmallow.fields.Integer()

    @functools.wraps(with_pagination_params)
    def inner(fn):
        # TODO: would be nice to manipulate the docs here as well
        @functools.wraps(fn)
        @load_query_params(PaginationParams)
        def inner_inner(*args, **kwargs):
            kwargs["page"] = max(kwargs.get("page", 1), 1)
            kwargs["results_per_page"] = min(
                max(kwargs.get("results_per_page", default_results_per_page), 1),
                default_results_per_page
            )

            return fn(*args, **kwargs)

        return inner_inner

    return inner

def with_cursor_params(default_results_per_page=50):
    """
    Validate and pass the standard parameters for cursor-paginated collections endpoints into a decorated
    MethodView method.
    """
    class CursorParams(marshmallow.Schema):
        max_id = marshmallow.fields.UUID()
        since_id = marshmallow.fields.UUID()
        results_per_page = marshmallow.fields.Integer()

    @functools.wraps(with_cursor_params)
    def inner(fn):
        @functools.wraps(fn)
        @load_query_params(CursorParams)
        def inner_inner(*args, **kwargs):
            kwargs["results_per_page"] = min(
                max(kwargs.get("results_per_page", default_results_per_page), 1),
                default_results_per_page
            )
            if kwargs.get("max_id") and kwargs.get("since_id"):
                abort(400, message="either of max_id and since_id may be passed, but not both")
            return fn(*args, **kwargs)

        return inner_inner

    return inner

Path = namedtuple("Path", ("args", "kwargs"))

class Spec:
    name = "dom-apispec"
    def __init__(self, app=None, **spec_kwargs):
        spec_kwargs.setdefault("plugins", [
            'apispec.ext.flask',
            'apispec.ext.marshmallow',
        ])

        self.spec = APISpec(**spec_kwargs, )
        self.app = None
        self.paths = []
        self._setup_shared()

        if app is not None:
            self.app = app
            self.init_app(app)

    ### pass through to spec
    def __getattr__(self, name):
        return getattr(self.spec, name)

    def init_app(self, app):
        if app.extensions.get(Spec.name) is None:
            app.extensions[Spec.name] = self
            with app.app_context():
                for path in self.paths:
                    self.real_add_path(*path.args, **path.kwargs)

    def add_path(self, *args, **kwargs):
        self.paths.append(Path(args, kwargs))
        self.real_add_path(*args, **kwargs)

    def real_add_path(self, *args, **kwargs):
        # single app env
        if self.app:
            with self.app.app_context():
                self.__add_path_from_current_app(*args, **kwargs)

        self.__add_path_from_current_app(*args, **kwargs)

    def __add_path_from_current_app(self, *args, **kwargs):
        do_add_path = False
        try:
            if flask.current_app.extensions.get(Spec.name) is self:
                do_add_path = True
        except RuntimeError:
            pass

        if do_add_path:
            view_class = kwargs.pop("view_class", None)
            if view_class is not None:
                for view_func in flask.current_app.view_functions.values():
                    if hasattr(view_func, "view_class") and view_func.view_class is view_class:
                        kwargs["view"] = view_func

            self.spec.add_path(*args, **kwargs)

    def register_resource(self, resource_class):
        self.add_path(view_class=resource_class)
        return resource_class

    def register_schema(self, name):
        @functools.wraps(self.register_schema)
        def inner(schema_class):
            self.spec.definition(name, schema=schema_class)
            return schema_class

        return inner

    def _setup_shared(self):
        self.add_parameter("api_version", "path",
                           description="api version for this request",
                           required=True,
                           type="string",
                           example="-")
        self.add_parameter("slug", "path",
                           description="unique name for this endpoint",
                           type="string",
                           example="slug")
        self.add_parameter("uuid", "path",
                           description="unique id for this endpoint",
                           type="string", format="uuid",
                           example="e50253ac-4dc2-11e8-aba3-0e1402415a00")
        self.add_parameter("page", "query",
                           description="which page to return for a paginated api",
                           type="int",
                           minimum=1,
                           example="1")
        self.add_parameter("results_per_page", "query", description="how many results to return per page",
                           type="int", example="25", minimum=1, maximum=50)

        @self.register_schema("Error")
        class ErrorSchema(marshmallow.Schema):
            message = marshmallow.fields.String(required=True)
