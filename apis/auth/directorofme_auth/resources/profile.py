'''
resources/profile.py -- The REST API for the profile resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with
from directorofme_flask_restful import resource_url

from . import api
from ..models import Profile as ProfileModel

@resource_url(api, "/profile/<string:id>", endpoint="profile_api")
class Profile(Resource):
    resource_type_map = {
        "id": fields.Url("profile_api"),
        "email": fields.String(),
        "preferences": fields.Raw
    }

    @marshal_with(resource_type_map)
    def get(self, **kwargs):
        return ProfileModel.query.get(kwargs["id"])
