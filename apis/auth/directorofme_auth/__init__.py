'''
The `directorofme_auth` package, providing data models and REST API access to
authentication and authorization functionality for directorofme.

@author: Matthew Story <matt@directorof.me>
'''
# ORDER MATTERS HERE
from .app import app, api
import resources
import models

__all__ = [ "app", "api", "resources", "models" ]
