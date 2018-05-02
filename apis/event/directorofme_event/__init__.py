import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_restful import Resource

from directorofme.flask import app_for_api
from directorofme.flask.api import Spec
from directorofme.authorization.orm import PermissionedQuery
from directorofme.authorization.groups import Scope
from directorofme.flask import versioned_api, Model, JWTManager

__all__ = [ "app", "api", "db", "jwt", "marshmallow", "migrate", "models", "resources" ]


api = versioned_api("event")
app = app_for_api(os.path.basename(os.path.dirname(__file__)), { "api_name": "event" })
app.register_blueprint(api.blueprint)

Model.__tablename_prefix__ = app.name
Model.__scope__ = Scope(display_name=app.name)

from . import models

db = SQLAlchemy(model_class=Model, query_class=PermissionedQuery)
db.init_app(app)
db.app = app
marshmallow = Marshmallow(app)

### TODO: Factor
spec = Spec(app, title='DirectorOf.Me Event API', version='0.0.1',)

from . import resources

@api.resource("/swagger.json", endpoint="spec_api")
class Spec(Resource):
    def get(self):
        return spec.to_dict()

jwt = JWTManager()
jwt.init_app(app)
jwt.app = app

migrate = Migrate(app, db, version_table=Model.version_table(), include_symbol=Model.include_symbol)
