'''
resources/session.py -- The REST API for the session resource.

@author: Matthew Story <matt@directorof.me>
'''
import datetime

from flask_restful import Resource, fields, marshal_with

from . import resource_url
from ..models import Session as SessionModel, Group as GroupModel

### TODO: make an example wrapper thing that holds the schema and examples
@resource_url("/session/<string:session_id>", endpoint="session_api")
class Session(Resource):
    resource_type_map = {
        "id": fields.Url("session_api"),
        "expires": fields.DateTime(dt_format='rfc822'),
        "app": fields.Url("app_api"),
        "profile": fields.Url("profile_api"),
        "groups": fields.List(fields.Url("group_api")),
        "environment": fields.Raw
    }

    @marshal_with(resource_type_map)
    def get(self, session_id):
        return SessionModel.query.get(session_id)
