'''
orm.py -- Auth support for a SQLAlchemy-based ORM.

@author: Matt Story <matt.story@directorof.me>
'''
import uuid
import enum
import functools
import contextlib

from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy import Column, String, or_, and_, orm
from sqlalchemy.event import listen
from sqlalchemy_utils import Timestamp, UUIDType, generic_repr

from . import standard_permissions, groups, exceptions

###: TODO factor out non-permissions stuff
###: TODO soft-deletes

__all__ = [ "Permission", "GroupBasedPermission", "PermissionedModelMeta", "PrefixedModel",
            "PermissionedModel", "Model", "PermissionedQuery" ]

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
        perms = {p for b in bases for p in getattr(b, "__perms__", []) }

        if __dict__.get("__standard_permissions__"):
            PermType = __dict__.get("__permission_type__", GroupBasedPermission)
            __dict__.update({k: PermType() for k in standard_permissions})
            perms |= set(standard_permissions)

        for kk,vv in __dict__.items():
            if isinstance(vv, Permission):
                if vv.name is not None and vv.name != kk:
                    raise ValueError("Perm name ({}) does not match "\
                                     "attribute name ({})".format(vv.name, kk))
                vv.name = kk
                perm_columns.update(cls.make_permissions(vv))
                perms.add(vv.name)

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


class _PermissionCheck(enum.Enum):
    granted = 1
    denied = 2
    not_denied = 3


class PermissionedModel(PrefixedModel):
    '''A model for handling group-based permissions transparently'''
    __abstract__ = True
    __standard_permissions__ = True
    __scope__ = None

    # map of query-type to (scope permission name, obj permission name)
    __select_perm__ = ("read", "read")
    __insert_perm__ = ("write", None)
    __update_perm__ = ("read", "write")
    __delete_perm__ = ("delete", "delete")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is None:
            for perm_name in self.__perms__:
                current_perms = getattr(self, perm_name)
                setattr(self, perm_name, current_perms if current_perms else self.default_perms(perm_name))

        self.update_initial_perms()


    @orm.reconstructor
    def update_initial_perms(self):
        self.__initial_perms__ = {p: getattr(self, p) for p in self.__perms__}

    @classmethod
    def default_perms(cls, perm_name):
        return tuple()

    @classmethod
    def permissions_enabled(cls):
        return True

    @classmethod
    def load_groups(cls):
        return []

    @classmethod
    @contextlib.contextmanager
    def disable_permissions(cls):
        '''Disable permissions as a decorator or context manager'''
        permissions_enabled = cls.permissions_enabled
        cls.permissions_enabled = lambda: False
        try:
            yield
        finally:
            cls.permissions_enabled = permissions_enabled

    @classmethod
    @contextlib.contextmanager
    def enable_permissions(cls):
        '''Disable permissions as a decorator or context manager'''
        permissions_enabled = cls.permissions_enabled
        cls.permissions_enabled = lambda: True
        try:
            yield
        finally:
            cls.permissions_enabled = permissions_enabled

    @classmethod
    def _scope_and_obj_perms_from_action(cls, action):
        try:
            return getattr(cls, "__{}_perm__".format(action))
        except AttributeError:
            raise ValueError("unsupported action: {}".format(action))

    @classmethod
    def _type_level_checks(cls, action):
        groups_list = cls.load_groups()

        # if there are no groups, permission is denied
        if not groups_list:
            return _PermissionCheck.denied

        # root always has permission
        if groups.root in groups_list:
            return _PermissionCheck.granted

        scope_perm_name, obj_perm_name = cls._scope_and_obj_perms_from_action(action)

        # check scope permissions
        scope_group = getattr(cls.__scope__, scope_perm_name, None)

        if scope_group is not None and scope_group not in groups_list:
            # if we don't have scope access permission is denied
            return _PermissionCheck.denied

        # if there are no object permissions for this action, permission is granted
        if obj_perm_name is None or getattr(cls, obj_perm_name, None) is None:
            return _PermissionCheck.granted

        return _PermissionCheck.not_denied


    @classmethod
    def permissions_criterion(cls, action):
        type_checks = cls._type_level_checks(action)

        if type_checks == _PermissionCheck.denied:
            return and_(False)
        elif type_checks == _PermissionCheck.granted:
            return and_(True)

        # build criterion from permissions columns
        parts = []
        perm = getattr(cls, cls._scope_and_obj_perms_from_action(action)[1])
        group_names = [g.name for g in cls.load_groups()]
        for col_number in range(perm.max_permissions):
            parts.append(getattr(cls, perm.column_name(col_number)).in_(group_names))

        return or_(*parts)

    def permissions_check(self, action):
        type_checks = self._type_level_checks(action)
        if type_checks == _PermissionCheck.denied:
            return False
        elif type_checks == _PermissionCheck.granted:
            return True

        groups_set = {g.name for g in self.load_groups()}
        obj_perms_set = set(self.__initial_perms__.get(self._scope_and_obj_perms_from_action(action)[1]))

        return bool(groups_set & obj_perms_set)


    @classmethod
    def insert_handler(cls, mapper, connection, target):
        if type(target).permissions_enabled() and not target.permissions_check("insert"):
            raise exceptions.PermissionDeniedError("Cannot insert type: {}".format(cls))

    @classmethod
    def update_handler(cls, mapper, connection, target):
        if type(target).permissions_enabled() and not target.permissions_check("update"):
            raise exceptions.PermissionDeniedError("Cannot update {}".format(target))

    @classmethod
    def delete_handler(cls, mapper, connection, target):
        if type(target).permissions_enabled() and not target.permissions_check("delete"):
            raise exceptions.PermissionDeniedError("Cannot delete {}".format(target))

    @classmethod
    def after_save_handler(cls, mapper, connection, target):
        target.update_initial_perms()


class PermissionedQuery(orm.Query):
    __actions__ = { "select", "insert", "update", "delete" }

    @classmethod
    def compile_handler(cls, query):
        if isinstance(query, cls):
            return query.permissions_filter("select")
        return query

    def permissions_filter(self, action):
        query = self

        if action not in self.__actions__:
            raise ValueError("Action must be one of {} (not {})".format(self.__actions__, action))

        for desc in self.column_descriptions:
            type_ = desc.get("type")
            if isinstance(type_, type) and issubclass(type_, PermissionedModel) and type_.permissions_enabled():
                query = self.enable_assertions(False).filter(type_.permissions_criterion(action))

        return query

    def _bulk_op(self, op_name, *op_args, **op_kwargs):
        '''Perform a bulk operation with permissions clauses appended to query'''
        return getattr(super(type(self), self.permissions_filter(op_name)), op_name)(*op_args, **op_kwargs)

    def update(self, *args, **kwargs):
        return self._bulk_op("update", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._bulk_op("delete", *args, **kwargs)

### The base model
@generic_repr("id")
class Model(PermissionedModel, Timestamp):
    __abstract__ = True

    #: Unique identifier for this object.
    id = Column(UUIDType, primary_key=True, default=uuid.uuid1)


### Attach Events
def _dispatch(classmethod_):
    @functools.wraps(classmethod_)
    def inner(*args, **kwargs):
        return classmethod_(*args, **kwargs)

    return inner

listen(PermissionedQuery, "before_compile", _dispatch(PermissionedQuery.compile_handler),
       retval=True, propagate=True)
listen(PermissionedModel, "before_insert", _dispatch(PermissionedModel.insert_handler), propagate=True)
listen(PermissionedModel, "before_update", _dispatch(PermissionedModel.update_handler), propagate=True)
listen(PermissionedModel, "before_delete", _dispatch(PermissionedModel.delete_handler), propagate=True)
listen(PermissionedModel, "after_insert", _dispatch(PermissionedModel.after_save_handler), propagate=True)
listen(PermissionedModel, "after_update", _dispatch(PermissionedModel.after_save_handler), propagate=True)
