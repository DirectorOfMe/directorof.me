'''
The `directorofme_auth` package, providing data models and REST API access to
authentication and authorization functionality for directorofme.

@author: Matthew Story <matt@directorof.me>
'''
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Resource
from directorofme.flask import versioned_api, directorofme_app, JWTManager
from directorofme.flask.api import Spec
from directorofme.authorization import groups, orm
from flask_marshmallow import Marshmallow
from directorofme.flask import DOMSQLAlchemy
from directorofme.events import DOMEventRegistry

__all__ = [ "app", "api", "config", "db", "exceptions", "jwt", "migrate", "marshmallow",
            "resources", "models", "spec", "dom_events" ]

# ORDER MATTERS HERE
dom_events = DOMEventRegistry()
from .config import config
config = config()

from . import exceptions

db = DOMSQLAlchemy(scope_name=config["name"])

from . import models

api = versioned_api(config.get("api_name"))
jwt = JWTManager()

marshmallow = Marshmallow()

app = directorofme_app(config["name"], config)
spec = Spec(marshmallow, title='DirectorOf.Me Event API', version='0.0.1',)
from . import resources

@api.resource("/swagger.json", endpoint="spec_api")
class Spec(Resource):
    def get(self):
        return spec.to_dict()

app.register_blueprint(api.blueprint)

db.init_app(app)
db.app = app

jwt.init_app(app)
jwt.app = app

marshmallow.init_app(app)
spec.init_app(app)


migrate = Migrate(app, db, version_table=db.Model.version_table(), include_symbol=db.Model.include_symbol)


@app.cli.command()
def push_refresh_token():
    print(app.config["PUSH_REFRESH_TOKEN"])


@app.cli.command()
def push_refresh_csrf_token():
    import sys
    import flask_jwt_extended as flask_jwt

    with app.app_context():
        print(flask_jwt.get_csrf_token(sys.stdin.read().strip()))
