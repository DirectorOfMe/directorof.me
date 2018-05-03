from flask_restful import Resource, abort

from . import api, spec
from ..models import App, InstalledApp

### TODO
@spec.register_resource
@api.resource("/event_types/<string:slug>", endpoint="event_types_api")
class App(Resource):
    """
    A endpoint for retrieving and manipulating application objects.
    """
