import functools
import flask

from collections import namedtuple
from apispec import APISpec

def dump_with_schema(Schema, **dump_kwargs):
    """
    Validate output and encode to a JSON serializable format via a marshmellow.Schema object.
    """
    @functools.wraps(dump_with_schema)
    def inner(fn):
        @functools.wraps(fn)
        def inner_inner(*args, **kwargs):
            obj = fn(*args, **kwargs)
            if obj is None:
                abort(404, message="No object found")

            return Schema().dump(obj, **dump_kwargs)

        return inner_inner

    return inner


def with_pagination_params(marshmallow):
    """
    Validate and pass the standard pagination parameters for collections endpoints into a decorated
    MethodView method.
    """
    class PaginationParams(marshmallow.Schema):
        page = marshmallow.Integer()
        results_per_page = marshmallow.Integer()

    @functools.wraps(with_pagination_params)
    def inner(fn):
        # TODO: woulc be nice to manipulate the docs here as well
        @functools.wraps(fn)
        def inner_inner(*args, **kwargs):
            kwargs.update(PaginationParams().dump(flask.request.values).data)
            kwargs["page"] = max(kwargs.get("page", 1), 1)
            kwargs["results_per_page"] = min(max(kwargs.get("results_per_page", 50), 1), 50)

            return fn(*args, **kwargs)

        return inner_inner

    return inner

Path = namedtuple("Path", ("args", "kwargs"))

class Spec:
    name = "dom-apispec"
    def __init__(self, app=None, **spec_kwargs):
        self.spec = APISpec(**spec_kwargs)
        self.app = app
        self.paths = []

        if app is not None:
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
