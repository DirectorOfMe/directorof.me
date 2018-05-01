import flask

from ..authorization import orm

__all__ = [ "Model" ]

class Model(orm.Model):
    __abstract__ = True

    @classmethod
    def default_perms(cls, perm_name):
        return flask.session.default_object_perms.get(perm_name, tuple())

    @classmethod
    def load_groups(cls):
        return flask.session.groups
