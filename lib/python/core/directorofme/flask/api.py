import uuid
import functools
import flask
import marshmallow

from flask_restful import Resource as FlaskResource, abort
from sqlalchemy.exc import IntegrityError

from collections import namedtuple
from apispec import APISpec

__all__ = [ "first_or_abort", "uuid_or_abort", "load_with_schema", "dump_with_schema",
            "with_pagination_params", "with_cursor_params", "Spec", "Resource" ]

def _abort_if_errors(result):
    if result.errors:
        messages = ["{}: {}".format(k,v) for k,v in result.errors.items()]
        abort(400, message="Validation failed: {}".format(", ".join(messages)))
    return result.data

def first_or_abort(query, status=404):
    obj = query.first()
    if obj is None:
        abort(status, message="Could not find object")
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


class Resource(FlaskResource):
    """Base DOM Resource"""
    @classmethod
    def paged(cls, query, page, results_per_page, order_by, **kwargs):
        """Return a collection-like dict for a paginated (not cursored) collection results set"""
        objs = query.order_by(order_by).limit(results_per_page + 1).offset((page - 1) * results_per_page).all()
        extra = objs.pop() if len(objs) > results_per_page else None

        collection = {
            "page": page,
            "next_page": page + (1 if extra else 0),
            "prev_page": max(page - 1, 1),
            "results_per_page": results_per_page,
            "collection": objs,
        }
        collection.update(kwargs)
        return collection

    @classmethod
    def generic_insert(cls, db, api, Model, data, url_field, url_cls=None):
        """Post helper method"""
        try:
            obj = Model(**data)
            db.session.add(obj)
            db.session.commit()
            return obj, 201, { "Location": api.url_for(url_cls or cls, **{url_field: getattr(obj, url_field)}) }
        except IntegrityError:
            db.session.rollback()
            abort(400, message="Please choose a unique name or slug")

    @classmethod
    def generic_update(cls, db, api, Model, url_field, url_value, data, url_cls=None, processor=None):
        """Patch/Put helper method"""
        obj = first_or_abort(db.session.query(Model).filter(getattr(Model, url_field) == url_value))
        url_value = getattr(obj, url_field)

        if processor:
            data = processor(data)

        for k,v in data.items():
            setattr(obj, k, v)

        try:
            db.session.add(obj)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(400, message="Please choose a unique name or slug")

        if getattr(obj, url_field) != url_value:
            return obj, 301, { "Location": api.url_for(url_cls or cls, **{ url_field: getattr(obj, url_field) }) }
        return obj

    @classmethod
    def generic_delete(cls, db, Model, url_field, url_value):
        """Delete helper"""
        db.session.delete(first_or_abort(db.session.query(Model).filter(getattr(Model, url_field) == url_value)))
        db.session.commit()
        return None, 204


Path = namedtuple("Path", ("args", "kwargs"))

class Spec:
    name = "dom-apispec"
    def __init__(self, ma, app=None, **spec_kwargs):
        spec_kwargs.setdefault("plugins", [
            'apispec.ext.flask',
            'apispec.ext.marshmallow',
        ])

        self.ma = ma
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

    def paginated_collection_schema(self, Nested, url, **kwargs):
        class PaginatedCollectionSchema(marshmallow.Schema):
            page = marshmallow.fields.Integer()
            results_per_page = marshmallow.fields.Integer()

            collection = self.ma.Nested(Nested, many=True)
            _links = self.ma.Hyperlinks({
                "self": self.ma.URLFor(url, **kwargs, page="<page>", results_per_page="<results_per_page>"),
                "next": self.ma.URLFor(url, **kwargs, page="<next_page>", results_per_page="<results_per_page>"),
                "prev": self.ma.URLFor(url, **kwargs, page="<prev_page>", results_per_page="<results_per_page>")
            })

        return PaginatedCollectionSchema

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
        self.add_parameter("email", "path",
                           description="email address for this profile",
                           type="string",
                           format="email",
                           example="test@example.com")
        self.add_parameter("id", "path",
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
        self.add_parameter("service", "path",
                           description="name of 3rd party service to authenticate against",
                           required=True,
                           type="string",
                           example="google")

        @self.register_schema("Error")
        class ErrorSchema(marshmallow.Schema):
            message = marshmallow.fields.String(required=True)
