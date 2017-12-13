'''
resources/group.py -- The REST API for the group resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with
from directorofme_flask_restful_fields import AttributedUrl

from . import resource_url
from ..models import Group as GroupModel

__all__ = [ "Group" ]

@resource_url("/group/<string:type>/<string:name>", endpoint="group_api")
class Group(Resource):
    resource_type_map = {
        "id": fields.Url("group_api"),
        "name": fields.String,
        "type": fields.String,
        "parent": fields.Url("group_api"),
        "parent": AttributedUrl("group_api", attribute="parent"),
    }

    @marshal_with(resource_type_map)
    def get(self, **kwargs):
        return GroupModel.query.get("/".join([kwargs["type"], kwargs["name"]]))
