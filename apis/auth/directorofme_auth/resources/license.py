'''
resources/license.py -- The REST API for the license resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with
from directorofme_flask_restful import fields as dom_fields, resource_url

from . import api
from ..models import License as LicenseModel

__all__ = [ "License" ]

@resource_url(api, "/license/<string:id>", endpoint="license_api")
class License(Resource):
    resource_type_map = {
        "id": fields.Url("license_api"),
        "groups": dom_fields.ModelUrlList("group_api"),
        "managing_group": dom_fields.AttributedUrl(
            "group_api", attribute="managing_group"
        ),
        "seats": fields.Integer,
        "profiles": dom_fields.ModelUrlList("profile_api")
    }

    @marshal_with(resource_type_map)
    def get(self, **kwargs):
        return LicenseModel.query.get(kwargs["id"])
