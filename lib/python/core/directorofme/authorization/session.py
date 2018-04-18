import uuid
import typing
import contextlib

import flask

from . import groups as groups_module
from ..specify import Spec, Attribute

__all__ = [ "SessionApp", "SessionProfile", "Session", "SessionDecorator", "do_with_groups", "do_as_root" ]

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
    #TODO: factor this to set
    groups = Attribute(typing.List[groups_module.Group])
    environment = Attribute(typing.Dict[str, typing.Any])

    def overwrite(self, new_session):
        for attr in self.attributes:
            setattr(self, attr, getattr(new_session, attr))


class SessionDecorator(contextlib.ContextDecorator):
    def __init__(self, extend_groups=True, real_session=flask.session, **session_modifications):
        self.real_session = real_session
        self.original_sessions = []
        self.extend_groups = extend_groups
        self.session_modifications = session_modifications
        super().__init__()

    def __enter__(self):
        self.original_sessions.append(Session.from_conforming_type(self.real_session))
        self.real_session.overwrite(self.copy_and_modify_session(self.original_sessions[-1]))

    def __exit__(self, exc_type, exc_value, traceback):
        self.real_session.overwrite(self.original_sessions.pop())

    def copy_and_modify_session(self, session):
        new_session = Session.from_conforming_type(session)
        for (name, value) in self.session_modifications.items():
            if name == "groups" and self.extend_groups:
                value = list(set(new_session.groups) | set(value))

            setattr(new_session, name, value)

        return new_session

# convenience methods
def do_with_groups(*groups, replace=False):
    groups = [groups_module.Group.from_conforming_type(g) for g in groups]
    return SessionDecorator(extend_groups=(not replace), groups=groups)

do_as_root = do_with_groups(groups_module.root)
