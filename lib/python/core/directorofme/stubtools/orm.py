'''
stubtools/orm.py -- dummy ORMs useful for stubbing out API requests and responses.

@author: Matt Story <matt@directorof.me>
'''

from . import exceptions

class Query:
    map_ = {}

    class ExampleQuery:
        def __init__(self, model, examples):
            self.model = model
            self.examples = examples

        def get(self, id_):
            if self.examples is None:
                raise exceptions.NotConfiguredError("No stub data provided")

            data = self.examples.get(id_)
            if None in (self.model, data):
                return data
            return self.model(**data)

    def __get__(self, instance, owner):
        key = id(owner)

        if not self.map_.get(key):
            self.map_[key] = self.ExampleQuery(owner, getattr(owner, "examples", None))

        return self.map_[key]


class Model:
    query = Query()

    def __init__(self, **contents):
        for k,v in contents.items():
            setattr(self, k, v)
