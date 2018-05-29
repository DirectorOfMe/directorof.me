from flask_restful import Resource, abort
from directorofme.authorization import groups, requires

from . import api, spec
from ..models import App, InstalledApp

@spec.register_resource
@api.resource("/apps/<string:slug>", endpoint="apps_api")
class App(Resource):
    """
    A endpoint for retrieving and manipulating applications
    """
    @spec.register_schema("AppRequestSchema")
    class AppRequestSchema(marshmallow.Schema):
        name = marshmallow.String(required=True)
        desc = marshmallow.String(required=True)
        url = marshmallow.Url(required=True)

        callback_url = marshmallow.Url(allow_none=True)
        config_schema = marshmallow.Dict(allow_none=True)
        public_key = marshmallow.String(allow_none=True)
        requested_access_groups = marsh

    #: OAuth callback URL.
    callback_url = Column(URLType)

    @spec.register_schema("AppResponseSchema")
    class AppResponseSchema(AppResponseSchema):
        slug = marshmallow.String(required=True)
        created = marshmallow.DateTime()
        updated = marshmallow.DateTime()

        _links = marshmallow.Hyperlinks({
            "self": marshmallow.URLFor("event.event_types_api", slug="<slug>"),
            "collection": marshmallow.URLFor("event.event_types_collection_api"),
        })
