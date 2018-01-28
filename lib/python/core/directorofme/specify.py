import typing

class Attribute:
    # support an optional type declaration which does nothing at present
    def __init__(self, type_: typing.Any = None) -> None:
        self.type = type_
        super().__init__()

    def __get__(self, cls, obj):
        if obj is not None:
            raise ValueError("value not initialized for instance")

        return self

class AttributeMeta(type):
    def __new__(cls, name, bases, __dict__):
        attrs = __dict__.setdefault("attributes", set())
        for name, attr in __dict__.items():
            if isinstance(attr, Attribute):
                attrs.add(name)

        return super().__new__(cls, name, bases, __dict__)


class Spec(metaclass=AttributeMeta):
    # convention
    attributes = []

    def __init__(self, **kwargs):
        for name, val in kwargs.items():
            if name in self.attributes:
                setattr(self, name, val)

    def __json_encode__(self):
        return {name: getattr(self, name) for name in self.attributes}

    @classmethod
    def from_conforming_type(cls, model: typing.Any) -> typing.Any:
        return cls({name: getattr(model, name) for name in cls.attributes})
