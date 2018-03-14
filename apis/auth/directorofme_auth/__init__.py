'''
The `directorofme_auth` package, providing data models and REST API access to
authentication and authorization functionality for directorofme.

@author: Matthew Story <matt@directorof.me>
'''

__all__ = [ "app", "api", "config", "db", "exceptions", "migrate", "resources", "models" ]

# ORDER MATTERS HERE
from . import exceptions
from .config import config
config = config()

from .models import db
from . import models

from .resources import api, jwt
from . import resources

from .app import app, migrate

#TODO: add in JWT or OpenID based auth headers
