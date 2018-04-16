'''
The `directorofme_auth` package, providing data models and REST API access to
authentication and authorization functionality for directorofme.

@author: Matthew Story <matt@directorof.me>
'''
import os

from flask_migrate import Migrate
from directorofme import flask_app

__all__ = [ "app", "api", "config", "db", "exceptions", "jwt", "migrate", "resources", "models" ]

# ORDER MATTERS HERE
from . import exceptions
from .models import db
from . import models
from .config import config
config = config()

from .resources import api, jwt
from . import resources

app = flask_app.api(config["name"], config)

app.register_blueprint(api.blueprint)

db.init_app(app)
db.app = app

jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db)
