import uuid
import typing

from . import groups
from ..specify import Spec, Attribute

__all__ = [ "SessionApp", "SessionProfile", "Session" ]

class SessionApp(Spec):
    '''JSON serializable application object'''
    id = Attribute(uuid.UUID)
    app_id = Attribute(uuid.UUID)
    app_name = Attribute(str)
    config = Attribute(typing.Dict[str, typing.Any])

class SessionProfile(Spec):
    '''JSON Serializable profile (user) object'''
    id = Attribute(uuid.UUID)
    email = Attribute(str)

class Session(Spec):
    '''The session object.'''
    ignored = ("save",)

    save = Attribute(bool)
    app = Attribute(SessionApp)
    profile = Attribute(SessionProfile)
    groups = Attribute(typing.List[groups.Group])
    environment = Attribute(typing.Dict[str, typing.Any])

    def overwrite(self, new_session):
        for attr in self.attributes:
            setattr(self, attr, getattr(new_session, attr))
