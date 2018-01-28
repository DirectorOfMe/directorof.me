### TODO: hook up to JWT
### TODO: hook up to Flask session interface
### TODO: Docs
### TODO: We should not call this stuff session
import uuid
import typing

from . import groups
from ..specify import Spec, Attribute

__all__ = [ "SessionApp", "SessionProfile", "Session" ]

class SessionApp(Spec):
    id = Attribute(uuid.UUID)
    app_id = Attribute(uuid.UUID)
    app_name = Attribute(str)
    config = Attribute(typing.Dict[str, typing.Any])

class SessionProfile(Spec):
    id = Attribute(uuid.UUID)
    email = Attribute(str)

class Session(Spec):
    '''The session object.'''
    id = Attribute(uuid.UUID)
    app = Attribute(SessionApp)
    profile = Attribute(SessionProfile)
    groups = Attribute(typing.List[groups.Group])
    environment = Attribute(typing.Dict[str, typing.Any])

    @classmethod
    def anonymous(cls) -> typing.Any:
        ### TODO: this
        return Session()
