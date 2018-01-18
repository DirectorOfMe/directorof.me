'''
resources/session.py -- The REST API for the session resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with
from directorofme_flask_restful import fields as dom_fields, resource_url

from . import api
from ..models import Session as SessionModel

__all__ = [ "Session" ]

### TODO: make an example wrapper thing that holds the schema and examples
@resource_url(api, "/session/<string:id>", endpoint="session_api")
class Session(Resource):
    resource_type_map = {
        "id": fields.Url("session_api"),
        "expires": fields.DateTime(dt_format='rfc822'),
        "installed_app": dom_fields.AttributedUrl(
            "installed_app_api", attribute="installed_app"
        ),
        "profile": dom_fields.AttributedUrl("profile_api", attribute="profile"),
        "groups": dom_fields.ModelUrlList("group_api"),
        "environment": fields.Raw
    }

    @marshal_with(resource_type_map)
    def get(self, **kwargs):
        return SessionModel.query.get(kwargs["id"])
