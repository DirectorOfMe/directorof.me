'''
orm.py -- Auth support for a SQLAlchemy-based ORM.

@author: Matt Story <matt.story@directorof.me>
'''
import uuid
import functools

import flask

from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, String, or_, orm
from sqlalchemy.event import listen
from sqlalchemy_utils import Timestamp, UUIDType, generic_repr
from slugify import slugify

from . import standard_permissions, groups

__all__ = [ "Permission", "GroupBasedPermission", "PermissionedModelMeta",
            "PrefixedModel", "PermissionedModel", "Model", "slugify_on_change" ]

def slugify_on_change(src, target, default=True):
    '''Class decorator that slugs an attribute when it changes and stores it
       to another attribute. By default it will automatically initialize the
       target value as well.

       NB: this does not play well with abstract classes or inheritence, and should only be used by
       concrete models.
    '''
    @functools.wraps(slugify_on_change)
    def inner(cls):
        if not hasattr(cls, "__table__") and not hasattr(cls, "__tablename__"):
            raise ValueError("May not be used with non-concrete models")

        old_init = cls.__init__
        def __init__(self, *args, **kwargs):
            old_init(self, *args, **kwargs)
            src_value = getattr(self, src, None)

            if src_value is not None:
                setattr(self, target, slugify(src_value))

        cls.__init__ = __init__

        listen(getattr(cls, src), "set", lambda obj, v, x, y: setattr(obj, target, slugify(v)))
        return cls

    return inner

class Permission:
    col_type = UUIDType

    permissions_prefix = "_permissions"
    permissions_delimiter = "_"

    def __new__(cls, *args, **kwargs):
        if cls is Permission:
            raise NotImplementedError("Permission is an abstract class")
        return super().__new__(cls)

    ### TODO: default protocol
    def __init__(self, name=None, max_permissions=2):
        self.name = name
        self.max_permissions = max_permissions

    ### Protocol used by PermissionedModelMeta
    @classmethod
    def make_column(cls):
        return Column(cls.col_type, nullable=True, index=True)

    def column_name(self, perm_number):
        if self.name is None:
            raise ValueError("`name` has not been initialized")

        return self.permissions_delimiter.join((
            self.__class__.permissions_prefix,
            self.name,
            str(perm_number)
        ))

    ### TODO: maybe make this a composite?
    ###   http://docs.sqlalchemy.org/en/latest/orm/composites.html
    ### get values from and to their respective columns
    def __get__(self, instance, owner):
        if instance is None:
            return self

        return tuple(perm for perm in self.permissions(instance) if perm is not None)

    ### XXX: should check against session, but probably not here
    def __set__(self, instance, value):
        value = tuple(value)
        if len(value) > self.max_permissions:
            raise ValueError(
                "cannot assign more than `{}` values".format(self.max_permissions)
            )

        for ii in range(self.max_permissions):
            try:
                setattr(instance, self.column_name(ii), value[ii])
            except IndexError:
                setattr(instance, self.column_name(ii), None)

    ### TODO: __del__

    def permissions(self, instance):
        for ii in range(self.max_permissions):
            yield getattr(instance, self.column_name(ii))



class GroupBasedPermission(Permission):
    ### without any foreign keys, this is just idiomatic for now
    col_type = String(50)

### Permissions Model Classes
class PermissionedModelMeta(DeclarativeMeta):
    def __new__(cls, object_or_name, bases, __dict__):
        perm_columns = {}
        perms = []

        if __dict__.get("__standard_permissions__"):
            PermType = __dict__.get("__permission_type__", GroupBasedPermission)
            __dict__.update({k: PermType() for k in standard_permissions})

        for kk,vv in __dict__.items():
            if isinstance(vv, Permission):
                if vv.name is not None and vv.name != kk:
                    raise ValueError("Perm name ({}) does not match "\
                                     "attribute name ({})".format(vv.name, kk))
                vv.name = kk
                perm_columns.update(cls.make_permissions(vv))
                perms.append(vv.name)

        __dict__.update(perm_columns)
        __dict__["__perms__"] = tuple(perms)

        return super().__new__(cls, object_or_name, bases, __dict__)

    def __init__(cls, object_or_name, bases, __dict__):
        prefix = getattr(cls, "__tablename_prefix__", None)
        table_name = getattr(cls, "__tablename__", None)

        if prefix is not None and table_name is not None:
            cls.__tablename__ = "_".join([prefix, table_name])

        super().__init__(object_or_name, bases, __dict__)

    @classmethod
    def make_permissions(cls, perm):
        perms = {}
        for ii in range(perm.max_permissions):
            perms[perm.column_name(ii)] = perm.make_column()
        return perms


PermissionedBase = declarative_base(metaclass=PermissionedModelMeta)

class PrefixedModel(PermissionedBase):
    __abstract__ = True
    __tablename_prefix__ = None

    @classmethod
    def version_table(cls):
        return cls.prefix_name("versions")

    @classmethod
    def include_symbol(cls, tablename, *args):
        prefix = cls.__tablename_prefix__
        if prefix:
            return tablename.startswith("_".join([prefix, ""]))
        return True

    @classmethod
    def prefix_name(cls, name):
        prefix = cls.__tablename_prefix__
        if prefix is not None:
            return "_".join([prefix, name])
        return name

class PermissionedModel(PrefixedModel):
    __abstract__ = True
    __standard_permissions__ = True
    __scope__ = None

    # map of query-type to permission name
    __select_perm__ = "read"
    __insert_perm__ = "write"
    __update_perm__ = "write"
    __delete_perm__ = "delete"

    ### TODO: populate these defaults from session
    def __init__(self, *args, **kwargs):
        for perm_name in self.__perms__:
            perm = kwargs.pop(perm_name, None)
            if perm is not None:
                setattr(self, perm_name, perm)

        super().__init__(*args, **kwargs)

    @classmethod
    def permissions_enabled(cls):
        return True

    @classmethod
    def load_groups(cls):
        return []

    @classmethod
    def load_groups_from_flask_session(cls):
        return flask.session.groups

    @classmethod
    def permission_criterion(cls, permission_name, groups_list):
        # if the groups list is empty, return a literal boolean FALSE criterion
        if not groups_list:
            return False

        # root group in session subverts access controls
        if groups.root in groups_list:
            return True

        criterion = []

        # if this model is scoped
        scope_group = getattr(cls.__scope__, permission_name, None)
        if scope_group is not None and scope_group not in groups_list:
            # if we don't have access we return a literal boolean FALSE criterion and short-circuit anything else
            return False

        # if we aren't root, we have groups and scope is OK
        perm = getattr(cls, permission_name)
        if perm:
            parts = []
            for col_number in range(perm.max_permissions):
                parts.extend([getattr(type_, perm.column_name(col_number)) == name for name in groups_list])

            return or_(*parts)

        return True

    @classmethod
    def compile_handler(cls, query):
        for desc in query.column_descriptions:
            type_ = desc.get("type")
            if isinstance(type_, PermissionedModelMeta) and type_.permissions_enabled():
                permissions_criterion = type_.permission_criterion(type_.__select_perm__, type_.load_groups())
                query = query.enable_assertions(False).filter(permissions_criterion)

        return query

listen(orm.Query, "before_compile", lambda query: PermissionedModel.compile_handler(query), retval=True)

### The base model
@generic_repr("id")
class Model(PermissionedModel, Timestamp):
    __abstract__ = True

    #: Unique identifier for this object.
    id = Column(UUIDType, primary_key=True, default=uuid.uuid1)
