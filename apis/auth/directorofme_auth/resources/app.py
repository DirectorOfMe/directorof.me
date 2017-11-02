'''
resources/app.py -- The REST API for the app resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with

from . import resource_url

@resource_url("/app/<string:app_id>", endpoint="app_api")
class App(Resource):
    pass

@resource_url("/app/<string:app_id>/installed/<string:id>", endpoint="installed_app_api")
class InstalledApp(Resource):
    pass
