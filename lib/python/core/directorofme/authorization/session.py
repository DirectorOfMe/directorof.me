### TODO: hook up to JWT
### TODO: hook up to Flask session interface
### TODO: Docs
### TODO: We should not call this stuff session
import uuid
import typing

import flask

from . import GroupTypes

__all__ = [ "SessionGroup", "SessionApp", "SessionProfile", "Session" ]

class SessionableAttribute:
    # support an optional type declaration which does nothing at present
    def __init__(self, type_: typing.Any = None) -> None:
        self.type = type_
        super().__init__()

    def __get__(self, cls, obj):
        if obj is not None:
            raise ValueError("value not initialized for instance")

        return self

class SessionableMeta(type):
    def __new__(cls, name, bases, __dict__):
        attrs = __dict__.setdefault("attributes", set())
        for name, attr in __dict__.items():
            if isinstance(attr, SessionableAttribute):
                attrs.add(name)

        return super().__new__(cls, name, bases, __dict__)


class Sessionable(metaclass=SessionableMeta):
    # convention
    attributes = []

    def __init__(self, **kwargs):
        for name, val in kwargs.items():
            if name in self.attributes:
                setattr(self, name, val)

    def __json_encode__(self):
        return {name: getattr(self, name) for name in self.attributes}

    @classmethod
    def from_model(cls, model: typing.Any) -> typing.Any:
        return cls({name: getattr(model, name) for name in cls.attributes})

class SessionGroup(Sessionable):
    id = SessionableAttribute(uuid.UUID)
    slug = SessionableAttribute(str)
    type = SessionableAttribute(GroupTypes)


class SessionApp(Sessionable):
    id = SessionableAttribute(uuid.UUID)
    app_id = SessionableAttribute(uuid.UUID)
    app_name = SessionableAttribute(str)
    config = SessionableAttribute(typing.Dict[str, typing.Any])

class SessionProfile(Sessionable):
    id = SessionableAttribute(uuid.UUID)
    email = SessionableAttribute(str)


class Session(Sessionable):
    '''The session object.'''
    id = SessionableAttribute(uuid.UUID)
    app = SessionableAttribute(SessionApp)
    profile = SessionableAttribute(SessionProfile)
    groups = SessionableAttribute(typing.List[SessionGroup])
    environment = SessionableAttribute(typing.Dict[str, typing.Any])

    @classmethod
    def anonymous(cls) -> typing.Any:
        ### TODO: this
        return Session()
