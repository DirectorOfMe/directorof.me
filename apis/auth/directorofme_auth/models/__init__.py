## placeholder class
## XXX: replace with SQLAlchemy
class Query:
    def __init__(self, examples):
        self.model = None
        self.examples = examples

    def get(self, id_):
        data = self.examples.get(id_)
        if self.model is None:
            return data
        return self.model(**data)

    def __set__(self, instance, owner):
        self.model = owner

class Model:
    def __init__(self, **contents):
        for k,v in contents.iteritems():
            setattr(self, k, v)

from session import Session
from group import Group
from profile import Profile
from app import App

__all__ = [ "Session", "Group", "Profile", "App" ]
