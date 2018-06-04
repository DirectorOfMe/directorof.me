import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_restful import Resource

from directorofme.flask import directorofme_app
from directorofme.client import DOM
from directorofme.flask.api import Spec
from directorofme.authorization.orm import PermissionedQuery
from directorofme.authorization.groups import Scope
from directorofme.flask import versioned_api, DOMSQLAlchemy, JWTManager

__all__ = [ "app", "api", "db", "jwt", "marshmallow", "migrate", "models", "resources", "push_client" ]

api = versioned_api("event")
app = directorofme_app(os.path.basename(os.path.dirname(__file__)), {
    "api_name": "event",
    "app": { k: os.environ.get(k) for k in ( "PUSH_REFRESH_TOKEN_FILE", "PUSH_REFRESH_CSRF_TOKEN_FILE" ) }
})
app.register_blueprint(api.blueprint)

push_client = DOM(
    domain=app.config["SERVER_NAME"],
    refresh_token=app.config["PUSH_REFRESH_TOKEN"],
    refresh_csrf_token=app.config["PUSH_REFRESH_CSRF_TOKEN"]
)

db = DOMSQLAlchemy(app)
from . import models

marshmallow = Marshmallow(app)

spec = Spec(marshmallow, app, title='DirectorOf.Me Event API', version='0.0.1',)
from . import resources

@api.resource("/swagger.json", endpoint="spec_api")
class Spec(Resource):
    def get(self):
        return spec.to_dict()

jwt = JWTManager(app)
migrate = Migrate(app, db, version_table=db.Model.version_table(), include_symbol=db.Model.include_symbol)
