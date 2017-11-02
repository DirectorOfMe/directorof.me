## placeholder class
## XXX: replace with SQLAlchemy
class Query:
    def __init__(self, examples):
        self.model = None
        self.examples = examples

    def get(self, id_):
        data = self.examples.get(id_)
        if None in (self.model, data):
            return data
        return self.model(**data)

    def __get__(self, instance, owner):
        self.model = owner
        return self

class Model:
    def __init__(self, **contents):
        for k,v in contents.items():
            setattr(self, k, v)

from .group import Group
from .profile import Profile
from .app import App
from .session import Session

__all__ = [ "Session", "Group", "Profile", "App" ]
