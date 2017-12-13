'''
resources/app.py -- The REST API for the app resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with
import directorofme_flask_restful_fields as dom_fields

from . import resource_url
from ..models import App as AppModel, InstalledApp as InstalledAppModel

@resource_url("/app/<string:id>", endpoint="app_api")
class App(Resource):
    resource_type_map = {
        "id": fields.Url("app_api"),
        "name": fields.String(),
        "url": fields.String(),
        "callback_url": fields.String(),
        "config_schema": fields.Raw,
        "groups": dom_fields.ModelUrlList("group_api"),
    }

    @marshal_with(resource_type_map)
    def get(self, **kwargs):
        return AppModel.query.get(kwargs["id"])

@resource_url("/app/<string:app_id>/<string:id>", endpoint="installed_app_api")
class InstalledApp(Resource):
    resource_type_map = {
        "id": fields.Url("installed_app_api"),
        "app_id": dom_fields.AttributedUrl("app_api", attribute="app"),
        "config": fields.Raw
    }

    @marshal_with(resource_type_map)
    def get(self, **kwargs):
        return InstalledAppModel.query.get("/".join([kwargs["app_id"], kwargs["id"]]))
