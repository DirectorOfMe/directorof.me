from directorofme.flask import versioned_api, JWTManager

from .. import config
api = versioned_api(config.get("api_name"))
jwt = JWTManager()

#from .group import Group
#from .profile import Profile
#from .app import App, InstalledApp
#from .session import Session
#from .license import License
#from .authenticate import google
from . import authenticate

__all__ = [ "api", "jwt", "Session", "Group", "Profile", "App", "InstalledApp", "License", "api", "authenticate" ]
