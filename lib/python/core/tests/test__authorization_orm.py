import pytest

from unittest import mock

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy_utils import UUIDType

from directorofme.authorization import orm

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


def test__slugify_on_change():
    init_mock = mock.Mock()

    @orm.slugify_on_change("name", "slug")
    class Slugify(declarative_base()):
        __tablename__ = "slugify_test"

        name = Column(String, primary_key=True)
        slug = Column(String)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            init_mock()

    @orm.slugify_on_change("name2", "slug2")
    class SlugifyNoInit(Slugify):
        name2 = Column(String)
        slug2 = Column(String)


    slugified = Slugify()
    assert init_mock.called, "Slugify.__init__ was called"

    assert slugified.name is None, "slug none if name not set"
    assert slugified.slug is None, "slug none if name not set"

    slugified.name = "test_Foo"
    assert slugified.slug == "test-foo", "slugified name set to slug"
    assert slugified.name == "test_Foo", "un-sluggified name set to name"

    slugified.name = "test_Bar"
    assert slugified.slug == "test-bar", "slugified name set on update to attr"

    slugified = Slugify(name="test_Baz")
    assert slugified.name == "test_Baz", "__init__ sets up name"
    assert slugified.slug == "test-baz", "__init__ sets up slug when not passed"

    slugified = Slugify(name="test_Foo_again", slug="slug")
    assert slugified.slug == "test-foo-again", "passed slug is overridden by slugified name"

    init_mock.reset_mock()
    no_init = SlugifyNoInit(name="test_Name", name2="test_Name 2")
    assert init_mock.called, "super().__init__ called by decorated sub-class"
    assert no_init.slug2 == "test-name-2", "sub-class slugger works"

    no_init.name2 = "test_Name2 again"
    assert no_init.slug2 == "test-name2-again", "update works on superclass"

    with pytest.raises(ValueError):
        orm.slugify_on_change("name", "slugged")(declarative_base())

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

        assert Permissioned.__perms__ == ("perm",), "perms tuple set correctly"

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

        assert NonAbstract.__perms__ == ("perm",), "perms tuple set correctly"

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

    def test__name_mismatch_raises(self):
        my_name_is = orm.GroupBasedPermission("my_name_is")
        with pytest.raises(ValueError):
            class ExtraPermissioned(Permissioned):
                something_else = my_name_is

    def test__tablename_prefix(self):
        class NonPrefixedNonAbstract(Base):
            __tablename__ = "non_prefixed"
            id = Column(UUIDType, primary_key=True)

        class PrefixedNonAbstract(Base):
            __tablename__ = "test"
            __tablename_prefix__ = "prefix"
            id = Column(UUIDType, primary_key=True)

        assert NonPrefixedNonAbstract.__tablename__ == "non_prefixed", "non-prefixed tablename works"
        assert PrefixedNonAbstract.__tablename__ == "prefix_test", "prefixed tablename works"


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


class Prefixed(orm.PrefixedModel):
    __tablename_prefix__ = "prefix"
    __tablename__ = "test_prefix"
    id = Column(UUIDType, primary_key = True)

class NonPrefixed(orm.PrefixedModel):
    __tablename__ = "test_non_prefixed"
    id = Column(UUIDType, primary_key = True)

class TestPrefixedModel:
    def test__tablename_basic(self):
        assert Prefixed.__tablename__ == "prefix_test_prefix", "PrefixedModel __tablename__ is prefixed"
        assert NonPrefixed.__tablename__ == "test_non_prefixed", "NonPrefixedModel __tablename__ is not prefixed"

    def test__version_table(self):
        assert Prefixed.version_table() == "prefix_versions", "versions directory is prefixed"
        assert NonPrefixed.version_table() == "versions", "versions directory is not prefixed"

    def test__prefix_name(self):
        assert Prefixed.prefix_name("foo") == "prefix_foo", "prefix_name with prefix set works"
        assert NonPrefixed.prefix_name("foo") == "foo", "prefix_name without prefix works"

    def test__include_symbol(self):
        assert Prefixed.include_symbol("prefix_foo"), "prefixed tablename returns true"
        assert not Prefixed.include_symbol("foo"), "non-prefixed tablename returns False"
        assert not Prefixed.include_symbol("different_foo"), "differently prefixed tablename returns False"

        assert NonPrefixed.include_symbol("prefix_foo"), "prefixed tablename returns true"
        assert NonPrefixed.include_symbol("foo"), "non-prefixed tablename returns true"


class Permed(orm.PermissionedModel):
    __tablename__ = "permisionedconcrete"
    id = Column(UUIDType, primary_key = True)


class TestPermissionedModel:
    def test__PermissionedModel_contract(self):
        assert isinstance(Permed.read, orm.GroupBasedPermission), "read installed"
        assert isinstance(Permed.write, orm.GroupBasedPermission), "write installed"
        assert isinstance(Permed.delete, orm.GroupBasedPermission), "delete installed"

        concrete = Permed()
        assert isinstance(concrete, orm.PrefixedModel), "permissionedmodel inherits prefixedmodel"
        concrete.read == tuple(), "read installed to instance"
        concrete.write == tuple(), "read installed to instance"
        concrete.delete == tuple(), "read installed to instance"

    def test__Permissions__init__(self):
        instance = Permed(read=("test", "groups"), write=("test",))
        assert instance.read == ("test", "groups"), "read set via __init__ kwarg"
        assert instance.write == ("test",), "write set via __init__ kwarg"
        assert instance.delete == tuple(), "delete not set when not passed"

        class ExtraPermed(Permed):
            fancy = orm.GroupBasedPermission()

        instance = ExtraPermed(fancy=("foo",))
        assert instance.fancy == ("foo",), "fancy perm set correctly"
        for perm in ("read", "write", "delete"):
            assert getattr(instance, perm) == tuple(), "{} not set".format(perm)

def test__Model_contract():
    class ConcreteModel(orm.Model):
        __tablename__ = "concrete_model"

    assert isinstance(ConcreteModel.id, InstrumentedAttribute), "id is a column"
    assert isinstance(ConcreteModel.id.type, UUIDType), "id is a uuid"
