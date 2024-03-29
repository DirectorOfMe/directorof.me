import uuid
import typing
import contextlib

import flask

from ..specify import Spec, Attribute
from . import groups as groups_module, requires as requires_module

__all__ = [ "SessionApp", "SessionProfile", "Session", "SessionDecorator", "do_with_groups", "do_as_root" ]

class SessionApp(Spec):
    '''JSON serializable application object'''
    id = Attribute(uuid.UUID)
    app_id = Attribute(uuid.UUID)
    app_slug = Attribute(str)

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
    default_object_perms = Attribute(typing.Dict[str, typing.Tuple[groups_module.Group]])

    def overwrite(self, new_session):
        for attr in self.attributes:
            setattr(self, attr, getattr(new_session, attr))

    @classmethod
    def empty(cls):
        return cls(save=False, app=None, profile=None, groups=[groups_module.everybody], environment={},
                   default_object_perms={ "read": (groups_module.everybody.name,) })

class SessionDecorator(contextlib.ContextDecorator):
    def __init__(self, extend_groups=True, real_session=None, **session_modifications):
        self.real_session = real_session or flask.session
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
class sudo(contextlib.ContextDecorator):
    def __init__(self, requires=groups_module.admin, do_as=groups_module.root):
        self.requires_decorator = requires_module.group(requires)
        self.session_decorator = SessionDecorator(groups=(do_as,))

    def __enter__(self):
        self.requires_decorator.__enter__()
        self.session_decorator.__enter__()

    def __exit__(self, *args):
        try:
            self.requires_decorator.__exit__(*args)
        finally:
            self.session_decorator.__exit__(*args)

def do_with_groups(*groups, replace=False):
    groups = [groups_module.Group.from_conforming_type(g) for g in groups]
    return SessionDecorator(extend_groups=(not replace), groups=groups)

do_as_root = do_with_groups(groups_module.root)
