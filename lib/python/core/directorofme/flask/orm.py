import flask

from flask_sqlalchemy import SQLAlchemy

from ..authorization import orm, groups

__all__ = [ "Model" ]

class Model(orm.Model):
    __abstract__ = True

    @classmethod
    def default_perms(cls, perm_name):
        return flask.session.default_object_perms.get(perm_name, tuple())

    @classmethod
    def load_groups(cls):
        return flask.session.groups

class DOMSQLAlchemy(SQLAlchemy):
    def __init__(self, app=None, scope_name=None):
        scope_name = scope_name or (None if app is None else app.name)
        if scope_name is None:
            raise ValueError("Either app or scope_name must be provided")

        class ScopedModel(Model):
            __abstract__ = True
            __tablename_prefix__ = scope_name
            __scope__ = groups.Scope(display_name=scope_name)

        super().__init__(app=app, model_class=ScopedModel, query_class=orm.PermissionedQuery)
