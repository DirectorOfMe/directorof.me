'''
resources/profile.py -- The REST API for the profile resource.

@author: Matthew Story <matt@directorof.me>
'''
from flask_restful import Resource, fields, marshal_with

from . import resource_url

@resource_url("/profile/<string:profile_id>", endpoint="profile_api")
class Profile(Resource):
    pass
