from .. import config
from directorofme_flask_restful import versioned_api
api = versioned_api(config.get("API_NAME"))

#from .group import Group
#from .profile import Profile
#from .app import App, InstalledApp
#from .session import Session
#from .license import License
#from .authenticate import google
from . import authenticate

__all__ = [ "api", "Session", "Group", "Profile", "App", "InstalledApp", "License", "api", "autheticate" ]
