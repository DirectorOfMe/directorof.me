from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy_utils import UUIDType

from directorofme import orm

import pytest


### Fixtures
class RandomPermission(orm.Permission):
    permissions_prefix = "_RANDOM"
    permissions_delimiter = "a"

    type_name = "random"
    rel = "random.id"

    def __init__(self, name=None, max_permissions=5):
        super().__init__(name=name, max_permissions=max_permissions)

class RandomlyPermissionedObject:
    random = RandomPermission("random")

    # actual vars
    def __init__(self):
        self._RANDOMarandoma0 = 567
        self._RANDOMarandoma1 = 890
        self._RANDOMarandoma2 = None
        self._RANDOMarandoma3 = None
        self._RANDOMarandoma4 = None

class TestPermission:
    def test__is_abstract(self):
        with pytest.raises(NotImplementedError):
            orm.Permission()
        assert isinstance(RandomPermission(), RandomPermission), "concrete works"

    def test__init_protocol(self):
        assert RandomPermission("foo").name == "foo", "positional name works"
        assert RandomPermission(name="foo").name == "foo", "named name works"
        assert RandomPermission().max_permissions == 5, \
               "max permissions defaults to 5"
        assert RandomPermission(max_permissions=3).max_permissions == 3, \
               "named max permissions works"

    def test__make_column(self):
        with pytest.raises(NotImplementedError):
            orm.Permission()

        column = RandomPermission.make_column()
        assert isinstance(column, Column), "concrete implementation returns a column"
        assert isinstance(column.type, UUIDType), "permission is an integer column"
        assert column.nullable, "permission is nullable"

    def test__column_name(self):
        class Basic(orm.Permission):
            rel = "foo.bar"

        basic = Basic()
        with pytest.raises(ValueError):
            basic.column_name(0)

        basic.name = "basic"
        assert basic.column_name(0) == "_permissions_basic_0", \
               "default column name works"

        perm = RandomPermission("random")
        assert perm.column_name(0) == "_RANDOMarandoma0", \
               "overrideing permissions prefix & delimiter works"

    def test__permissions(self):
        instance = RandomlyPermissionedObject()
        perms = tuple(RandomlyPermissionedObject.random.permissions(instance))
        assert perms == (567, 890, None, None, None), \
               "permissions method returns correct values"

    def test__permission_descriptor__get__(self):
        assert isinstance(RandomlyPermissionedObject.random, RandomPermission), \
               "class access returns the permission object"

        instance = RandomlyPermissionedObject()
        assert isinstance(instance.random, tuple), "instance access returns a tuple"
        assert instance.random == (567, 890), "instance returns correct values"

    def test__permission_descriptor__set__(self):
        instance = RandomlyPermissionedObject()
        instance.random = (123,)

        assert instance.random == (123,), "instance __get__ works after reset"
        assert isinstance(RandomlyPermissionedObject.random, RandomPermission), \
               "class access is still the permission after reset"

        perms = tuple(RandomlyPermissionedObject.random.permissions(instance))
        assert perms == (123, None, None, None, None), \
               "setting perms resets all perms"

        with pytest.raises(ValueError):
            instance.random = range(6)
        assert instance.random == (123,), "failed set failed in full"

def test__GroupBasedPermission__contract():
    column = orm.GroupBasedPermission.make_column()
    assert isinstance(column, Column), "concrete implementation returns a column"
    assert isinstance(column.type, String), "permission is an integer column"
    assert column.nullable, "permission is nullable"

### Fixtures
Base = declarative_base(metaclass=orm.PermissionedModelMeta)
class Permissioned(Base):
    __abstract__ = True
    perm = RandomPermission()

### Tests
class TestPermissionedModelMeta:
    def test__adds_perms_to_class(self):
        '''Test that perms are added'''
        for ii in range(Permissioned.perm.max_permissions):
            column = Permissioned.__dict__[Permissioned.perm.column_name(ii)]
            assert isinstance(column, Column), \
                   "permission {} was added to an abstract model".format(ii)

            column = getattr(Permissioned, Permissioned.perm.column_name(ii))
            assert isinstance(column, Column), \
                   "permission {} was added to an abstract model".format(ii)

        class NonAbstract(Base):
            __tablename__ = "hi"
            perm = RandomPermission()
            id = Column(UUIDType, primary_key=True)

        for ii in range(NonAbstract.perm.max_permissions):
            column = NonAbstract.__dict__[NonAbstract.perm.column_name(ii)]
            assert isinstance(column, InstrumentedAttribute), \
                   "permission {} was added to a concrete model".format(ii)

            column = getattr(NonAbstract, NonAbstract.perm.column_name(ii))
            assert isinstance(column, InstrumentedAttribute), \
                   "permission {} was added to a concrete model".format(ii)

    def test__make_permissions(self):
        cols = orm.PermissionedModelMeta.make_permissions(Permissioned.perm)
        keys_should_be = (
            "_RANDOMaperma0",
            "_RANDOMaperma1",
            "_RANDOMaperma2",
            "_RANDOMaperma3",
            "_RANDOMaperma4"
        )
        assert keys_should_be == tuple(sorted(cols.keys())), \
            "correct attribute names are generated by make_permissions"

        for col in cols.values():
            assert isinstance(col, Column), "make_permissions values are Columns"

def test__PermissionedBase_works():
    perm = orm.GroupBasedPermission()
    class ReadOnlyModel(orm.PermissionedBase):
        __abstract__ = True
        read = perm

    assert ReadOnlyModel.read is perm, "permission installed to class"

    class Concrete(ReadOnlyModel):
        __tablename__ = "concrete"
        id = Column(UUIDType, primary_key = True)

    concrete = Concrete()
    assert concrete.read == tuple(), "permission descriptor get is working"
    concrete.read = ["read"]
    assert concrete.read == ("read",), "permission descriptor set is working"
    assert concrete._permissions_read_0 == "read", "permission attrs set correctly"
    assert concrete._permissions_read_1 == None, "permission attrs set correctly"


def test__PermissionedModel_contract():
    class Permed(orm.PermissionedModel):
        __tablename__ = "permisionedconcrete"
        id = Column(UUIDType, primary_key = True)

    assert isinstance(Permed.read, orm.GroupBasedPermission), "read installed"
    assert isinstance(Permed.write, orm.GroupBasedPermission), "write installed"
    assert isinstance(Permed.delete, orm.GroupBasedPermission), "delete installed"

    concrete = Permed()
    concrete.read == tuple(), "read installed to instance"
    concrete.write == tuple(), "read installed to instance"
    concrete.delete == tuple(), "read installed to instance"


def test__Model_contract():
    class ConcreteModel(orm.Model):
        __tablename__ = "concrete_model"

    assert isinstance(ConcreteModel.id, InstrumentedAttribute), "id is a column"
    assert isinstance(ConcreteModel.id.type, UUIDType), "id is a uuid"
