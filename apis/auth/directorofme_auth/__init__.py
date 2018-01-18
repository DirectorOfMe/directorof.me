'''
The `directorofme_auth` package, providing data models and REST API access to
authentication and authorization functionality for directorofme.

@author: Matthew Story <matt@directorof.me>
'''
# ORDER MATTERS HERE
from .app import app, api
# TODO: Hook this back up
# from . import resources
from . import models

#TODO: add in JWT or OpenID based auth headers

__all__ = [ "app", "api", "resources", "models" ]
