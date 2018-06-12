import os

import flask

from flask_restful import Resource
from flask_marshmallow import Marshmallow

from directorofme import DOMEventRegistry
from directorofme.oauth import Client
from directorofme.crypto import RSACipher
from directorofme.flask import versioned_api, directorofme_app, JWTManager
from directorofme.flask.api import Spec

from .config import config

__all__ = [ "app" ]

api = versioned_api(config.get("api_name"))
app = directorofme_app(config["name"], config)
app.register_blueprint(api.blueprint)

jwt = JWTManager(app)
marshmallow = Marshmallow(app)
spec = Spec(marshmallow, app=app, title='DirectorOf.Me Calendar API', version='0.0.1',)
cipher = RSACipher(config["CALENDAR_PUBLIC_KEY"], config["CALENDAR_PRIVATE_KEY"])

dom_events = DOMEventRegistry()

from . import handlers
from . import resources

@api.resource("/swagger.json", endpoint="spec_api")
class Spec(Resource):
    def get(self):
        return spec.to_dict()

