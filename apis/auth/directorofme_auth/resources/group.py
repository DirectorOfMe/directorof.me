'''
resources/group.py -- The REST API for the group resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with

from . import resource_url

@resource_url("/group/<string:group_type>/<string:group_id>", endpoint="group_api")
class Group(Resource):
    pass
