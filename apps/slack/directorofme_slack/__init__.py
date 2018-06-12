import os

import flask

from flask_restful import Resource
from flask_marshmallow import Marshmallow

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
spec = Spec(marshmallow, app=app, title='DirectorOf.Me Slack API', version='0.0.1',)
cipher = RSACipher(config["SLACK_PUBLIC_KEY"], config["SLACK_PRIVATE_KEY"])

from .bot import Bot
from . import dom_events
dom_events = dom_events.DOMBotEventRegistry()

from . import handlers
from . import resources

@api.resource("/swagger.json", endpoint="spec_api")
class Spec(Resource):
    def get(self):
        return spec.to_dict()

