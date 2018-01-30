'''
orm.py -- Auth support for a SQLAlchemy-based ORM.

@author: Matt Story <matt.story@directorof.me>
'''
import uuid

from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy import Column, String
from sqlalchemy_utils import Timestamp, UUIDType, generic_repr

__all__ = [ "Permission", "GroupBasedPermission", "PermissionedModelMeta",
            "PermissionedModel", "Model" ]

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
    col_type = String(20)

### Permissions Model Classes
class PermissionedModelMeta(DeclarativeMeta):
    def __new__(cls, object_or_name, bases, __dict__):
        perm_columns = {}
        perms = []

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

    @classmethod
    def make_permissions(cls, perm):
        perms = {}
        for ii in range(perm.max_permissions):
            perms[perm.column_name(ii)] = perm.make_column()
        return perms


PermissionedBase = declarative_base(metaclass=PermissionedModelMeta)

class PermissionedModel(PermissionedBase):
    __abstract__ = True
    read = GroupBasedPermission()
    write = GroupBasedPermission()
    delete = GroupBasedPermission()
    ### TODO: populate these defaults from session

    def __init__(self, *args, **kwargs):
        for perm_name in self.__perms__:
            perm = kwargs.pop(perm_name, None)
            if perm is not None:
                setattr(self, perm_name, perm)

        super().__init__(*args, **kwargs)

### The base model
@generic_repr("id")
class Model(PermissionedModel, Timestamp):
    __abstract__ = True

    #: Unique identifier for this object.
    id = Column(UUIDType, primary_key=True, default=uuid.uuid1)
