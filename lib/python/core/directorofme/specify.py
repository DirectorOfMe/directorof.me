import typing

__all__ = [ "Attribute", "AttributeMeta", "Spec", "undefaulted" ]

# sentinel
undefaulted = object()

class Attribute:
    # support an optional type declaration which does nothing at present
    def __init__(self, type_: typing.Any = None, default = undefaulted) -> None:
        self.type = type_
        self.default = default
        super().__init__()

    def __get__(self, obj, cls):
        if obj is not None:
            raise ValueError("value not initialized for instance")

        return self

class AttributeMeta(type):
    def __new__(cls, name, bases, __dict__):
        attrs = __dict__.setdefault("attributes", set())
        for attr_name, attr in __dict__.items():
            if isinstance(attr, Attribute):
                attrs.add(attr_name)

        return super().__new__(cls, name, bases, __dict__)


class Spec(metaclass=AttributeMeta):
    # convention
    attributes = []

    def __init__(self, **kwargs):
        seen_attrs = set()
        for name, val in kwargs.items():
            if name in self.attributes:
                setattr(self, name, val)
                seen_attrs.add(name)

        for unseen in self.attributes - seen_attrs:
            attr = getattr(self.__class__, unseen)
            if attr.default is not undefaulted:
                setattr(self, unseen, attr.default)

    def __json_encode__(self):
        return {name: getattr(self, name) for name in self.attributes}

    @classmethod
    def from_conforming_type(cls, model: typing.Any) -> typing.Any:
        return cls(**{name: getattr(model, name) for name in cls.attributes})
