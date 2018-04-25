from flask_sqlalchemy import SQLAlchemy
from directorofme.authorization import orm
from directorofme.authorization.flask import Model

__all__ = ["db", "Group", "GroupTypes", "License", "Profile", "App", "InstalledApp", "exceptions"]

db = SQLAlchemy(model_class=Model, query_class=orm.PermissionedQuery)

from . import exceptions
from .group import Group, GroupTypes
from .app import App, InstalledApp
from .license import License
from .profile import Profile
