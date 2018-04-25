import uuid
import pytest

from unittest import mock

from sqlalchemy import Column, String, and_, create_engine, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy_utils import UUIDType

from directorofme.authorization import orm, groups, exceptions, standard_permissions

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
    __table_args = {"sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True)


class TestPermissionedModel:
    def test__PermissionedModel_contract(self):
        assert isinstance(Permed.read, orm.GroupBasedPermission), "read installed"
        assert isinstance(Permed.write, orm.GroupBasedPermission), "write installed"
        assert isinstance(Permed.delete, orm.GroupBasedPermission), "delete installed"

        concrete = Permed()
        assert isinstance(concrete, orm.PrefixedModel), "permissionedmodel inherits prefixedmodel"
        assert concrete.read == tuple(), "read installed to instance"
        assert concrete.write == tuple(), "read installed to instance"
        assert concrete.delete == tuple(), "read installed to instance"

        # overridable attrs affecting perms
        assert concrete.__scope__ is None, "scope defaults to None"
        assert concrete.__select_perm__ == ("read", "read"), "select perm defaults"
        assert concrete.__insert_perm__ == ("write", None), "insert perm defaults"
        assert concrete.__update_perm__ == ("read", "write"), "insert perm defaults"
        assert concrete.__delete_perm__ == ("delete", "delete"), "insert perm defaults"

    def test__PermissionedModel__init__(self):
        instance = Permed(read=("test", "groups"), write=("test",))
        assert instance.read == ("test", "groups"), "read set via __init__ kwarg"
        assert instance.write == ("test",), "write set via __init__ kwarg"
        assert instance.delete == tuple(), "delete not set when not passed"
        assert instance.__initial_perms__ == {"read": ("test", "groups"), "write": ("test",), "delete": tuple()},\
               "initial perms set from initializing perms"

        class ExtraPermed(Permed):
            fancy = orm.GroupBasedPermission()

        instance = ExtraPermed(fancy=("foo",))
        assert instance.fancy == ("foo",), "fancy perm set correctly"
        for perm in ("read", "write", "delete"):
            assert getattr(instance, perm) == tuple(), "{} not set".format(perm)

    @mock.patch.object(orm.PermissionedModel, "default_perms")
    def test__default_perms(self, default_perms_mock):
        default_perms_mock.return_value = ("default-group-name",)

        for perm in standard_permissions:
            assert getattr(Permed(), perm) == ("default-group-name",), "defaults correctly"

        instance = Permed(read=("foo",), delete=("bar",))
        assert instance.read == ("foo",), "when passed, default is not set"
        assert instance.delete == ("bar",), "when passed, default is not set"
        assert instance.write == ("default-group-name",), "when not passed default is set"

    def test__overridable_method_defaults(self, request_context_with_session):
        assert orm.PermissionedModel.permissions_enabled(), "permissions_enabled defaults to True"
        assert orm.PermissionedModel.load_groups() == [], "load_groups returns an empty list by default"

    # 286-296, 301-302, 306-307, 311-312
    def test__permissions_criterion_and_permissions_check(self):
        assert str(Permed.permissions_criterion("select")) == "false",\
               "empty groups list returns literal False criteria (e.g. with no groups permission is denied"
        assert Permed().permissions_check("select") is False, "empty groups list means no permissions"

        with mock.patch.object(Permed, "load_groups") as mock_load:
            mock_load.return_value = [groups.everybody, groups.root]
            assert Permed.load_groups() == mock_load.return_value, "mock installed"
            assert str(Permed.permissions_criterion("select")) == "true",\
                   "if root is in groups_list a literal True criteria is returned (root always has permission)"

            assert Permed().permissions_check("select") is True, "root always has permission"

        yes_scope = groups.Scope(display_name="yes")
        with mock.patch.object(Permed, "load_groups") as mock_load:
            mock_load.return_value = [groups.everybody, yes_scope.read, yes_scope.write]
            assert Permed.load_groups() == mock_load.return_value, "mock installed"
            for meth in (Permed.permissions_criterion, Permed().permissions_check):
                with pytest.raises(ValueError):
                    meth("no_action")

            with mock.patch.object(Permed, "__scope__", groups.Scope(display_name="nope")):
                assert str(Permed.permissions_criterion("select")) == "false",\
                       "if correct scope permission is not in groups list a literal False criteria is returned"

                assert Permed().permissions_check("select") is False, \
                       "if correct scope permission is not in groups list a permission is denied"

            with mock.patch.object(Permed, "__scope__", yes_scope):
                assert str(Permed.permissions_criterion("insert")) == "true",\
                       "if correct scope permission is in groups list and action is insert, permission is granted"
                assert Permed().permissions_check("insert") is True, \
                       "if correct scope permission is in groups list and action is insert, permission is granted"

                with mock.patch.object(Permed, "read", None):
                    assert str(Permed.permissions_criterion("select")) == "true",\
                        "if permission is not defined on object then permission is not enforced"
                    assert Permed().permissions_check("select") is True,\
                        "if permission is not defined on object then permission is not enforced"

        with mock.patch.object(Permed, "load_groups") as mock_load:
            # this is actually how SQLAlchemy tests conditions
            mock_load.return_value = [groups.user, groups.everybody]
            assert Permed.load_groups() == mock_load.return_value, "mock installed"
            assert str(Permed.permissions_criterion("select")) ==  \
                   "{t}.{perm}_0 IN (:{perm}_0_1, :{perm}_0_2) OR {t}.{perm}_1 IN (:{perm}_1_1, :{perm}_1_2)"\
                   "".format(t=Permed.__tablename__, perm="_permissions_read")

            with mock.patch.object(Permed, "read", [groups.user.name]):
                assert Permed().permissions_check("select") is True, "permissions check works when group in list"

            with mock.patch.object(Permed, "read", []):
                assert Permed().permissions_check("select") is False, \
                       "permissions check works when group not in list"

    @mock.patch.object(Permed, "load_groups")
    def test__initial_perms_are_what_matters(self, mock_load):
        mock_load.return_value = [groups.everybody]
        assert Permed.load_groups() == mock_load.return_value, "mock installed"

        no_initial_perms = Permed()
        assert no_initial_perms.permissions_check("select") is False, "no groups means no access"

        no_initial_perms.read = (groups.everybody.name,)
        assert no_initial_perms.permissions_check("select") is False, "even after read set, no access"

        Permed(read=[groups.everybody]).permissions_check("select") is True, "works when initialized with access"

    def test__insert_handler(self, bound_session_with_permed):
        # no groups fails
        permed = Permed()
        bound_session_with_permed.add(permed)
        with pytest.raises(exceptions.PermissionDeniedError):
            bound_session_with_permed.commit()

        # disabled permissions succeeds
        bound_session_with_permed.rollback()
        bound_session_with_permed.add(permed)
        with orm.PermissionedModel.disable_permissions():
            bound_session_with_permed.commit()
            assert isinstance(permed.id, int), "permed saved"

        permed_scope = groups.Scope(display_name="permed")
        with mock.patch.object(Permed, "load_groups") as mock_load, \
                mock.patch.object(Permed, "__scope__", permed_scope):
            mock_load.return_value = [permed_scope.write, permed_scope.read, groups.user]
            scoped = Permed(read=(groups.user.name,))
            bound_session_with_permed.add(scoped)
            bound_session_with_permed.commit()
            assert isinstance(scoped.id, int), "scoped saved"

    @orm.PermissionedModel.disable_permissions()
    def test__after_save_handler(self, bound_session_with_permed):
        permed = Permed()
        permed.read = (groups.everybody.name,)
        assert permed.__initial_perms__["read"] == tuple(), "initial perms remain unchanged"

        bound_session_with_permed.add(permed)
        bound_session_with_permed.commit()
        assert permed.__initial_perms__["read"] == (groups.everybody.name,), "initial perms set after insert"

        permed.write = (groups.user.name,)
        assert permed.__initial_perms__["write"] == tuple(), "initial perms remain unchanged"
        bound_session_with_permed.add(permed)
        bound_session_with_permed.commit()
        assert permed.__initial_perms__["write"] == (groups.user.name,), "initial perms set after update"

    @mock.patch.object(Permed, "load_groups")
    def test__update_handler(self, mock_load, bound_session_with_permed):
        # no groups fails
        mock_load.return_value = [groups.everybody,]
        assert Permed.load_groups() == [groups.everybody], "perms mock works"

        permed = Permed(read=(groups.everybody.name,))
        bound_session_with_permed.add(permed)
        with orm.PermissionedModel.disable_permissions():
            bound_session_with_permed.commit()

        assert isinstance(permed.id , int), "permed saved"

        # update fails if no model-level permission
        permed.write = (groups.everybody.name,)
        bound_session_with_permed.add(permed)
        with pytest.raises(exceptions.PermissionDeniedError):
            bound_session_with_permed.commit()

        bound_session_with_permed.rollback()

        permed.write = (groups.everybody.name,)
        bound_session_with_permed.add(permed)
        with orm.PermissionedModel.disable_permissions():
            bound_session_with_permed.commit()

        # update succeeds with model write permission
        permed.read = (groups.everybody.name, groups.user.name)
        bound_session_with_permed.add(permed)
        bound_session_with_permed.commit()

        permed_scope = groups.Scope(display_name="permed")
        with mock.patch.object(Permed, "__scope__", permed_scope):
            permed.delete = (groups.user.name,)
            bound_session_with_permed.add(permed)

            # fail without scope-level read
            with orm.PermissionedModel.disable_permissions():
                bound_session_with_permed.commit()

            bound_session_with_permed.rollback()
            bound_session_with_permed.add(permed)

            mock_load.return_value += [permed_scope.read]
            bound_session_with_permed.commit()
            assert isinstance(permed.id, int), "update works with scope read"

    @mock.patch.object(Permed, "load_groups")
    def test__delete_handler(self, mock_load, bound_session_with_permed):
        # no groups fails
        mock_load.return_value = [groups.everybody,]
        assert Permed.load_groups() == [groups.everybody], "perms mock works"

        def make_permed(add_delete=True):
            with orm.PermissionedModel.disable_permissions():
                permed = Permed(read=(groups.everybody.name,), write=(groups.everybody.name,))
                permed.delete = (groups.everybody.name,) if add_delete else tuple()
                bound_session_with_permed.add(permed)
                bound_session_with_permed.commit()
                assert isinstance(permed.id, int), "permed created"
                return permed

        bound_session_with_permed.delete(make_permed(False))
        with orm.PermissionedModel.disable_permissions():
            bound_session_with_permed.commit()

        bound_session_with_permed.rollback()

        # modify the delete group -- works without scope
        permed = make_permed()
        bound_session_with_permed.delete(permed)
        bound_session_with_permed.commit()
        assert bound_session_with_permed.query(Permed).filter(Permed.id == permed.id).first() is None, \
               "actually deleted"

        permed_scope = groups.Scope(display_name="permed")
        with mock.patch.object(Permed, "__scope__", permed_scope):
            bound_session_with_permed.delete(make_permed())
            with pytest.raises(exceptions.PermissionDeniedError):
                bound_session_with_permed.commit()
            bound_session_with_permed.rollback()

            mock_load.return_value += [permed_scope.delete]
            bound_session_with_permed.delete(make_permed())
            bound_session_with_permed.commit()


    def test__disable_permissions(self):
        assert orm.PermissionedModel.permissions_enabled(), "permissions_enabled defaults to true"
        with orm.PermissionedModel.disable_permissions():
            assert not orm.PermissionedModel.permissions_enabled(), "override of permissions_enabled works"
        assert orm.PermissionedModel.permissions_enabled(), "permissions_enabled reset after exit"


class NoPerms(Permed):
    @classmethod
    def permissions_enabled(cls):
        return False

class AlwaysAsUser(Permed):
    select_whereclause = ""\
        "permisionedconcrete.id = :id_1 AND ("\
            "{t}.{perm}_0 IN (:{perm}_0_1, :{perm}_0_2) OR {t}.{perm}_1 IN (:{perm}_1_1, :{perm}_1_2)"\
        ")".format(t=Permed.__tablename__, perm="_permissions_read")

    @classmethod
    def load_groups(cls):
        return [groups.everybody, groups.user]

class NotSubclass(Permissioned):
    __abstract__ = False
    __tablename__ = "not_subclass"

    id = Column(UUIDType, primary_key = True)

@pytest.fixture
def Session():
    return sessionmaker(query_cls=orm.PermissionedQuery)

@pytest.fixture
def session(Session):
    return Session()

@pytest.fixture
def engine():
    return create_engine('sqlite://')

@pytest.fixture
def bound_session(Session, engine):
    return Session(bind=engine)

@pytest.fixture
def bound_session_with_permed(engine, bound_session):
    Permed.__table__.create(engine)
    try:
        yield bound_session
    finally:
        Permed.__table__.drop(engine)

class TestPermissionedQuery:
    def test__compile_handler(self, session):
        query = session.query(NoPerms)
        assert query.compile_handler(query).whereclause is None, \
               "no clauses added when permissioned_enabled returns false"


        with mock.patch("directorofme.authorization.orm.PermissionedQuery.permissions_filter") as perm_filter:
            assert query.compile_handler(None) is None, "if instance is not a PermissionedQuery No-Op"
            assert not perm_filter.called, "perm filter should not have been called"

        query = session.query(AlwaysAsUser).filter(AlwaysAsUser.id == 1)
        assert str(query.compile_handler(query).whereclause) == AlwaysAsUser.select_whereclause, \
               "direct call to compile handler with permissions works as expected"

        assert str(query).endswith(AlwaysAsUser.select_whereclause), "compile_handler called by `before_compile`"


    def test__permissions_filter(self, session):
        with pytest.raises(ValueError):
            session.query(NoPerms).permissions_filter("nope")

        assert session.query(NotSubclass).permissions_filter("select").whereclause is None, \
               "permissions skipped if the model isn't a PermissionedModel"

        assert str(
            session.query(AlwaysAsUser).filter(AlwaysAsUser.id == 1).permissions_filter("select").whereclause
        ) == AlwaysAsUser.select_whereclause,  "permissions_filter is correct when called"

        with orm.PermissionedModel.disable_permissions():
            assert session.query(AlwaysAsUser).permissions_filter("select").whereclause is None, \
                   "no filtering if permissions are disabled"

    @mock.patch("sqlalchemy.orm.Query.update")
    @mock.patch("sqlalchemy.orm.Query.delete")
    def test__bulk_operations_happypath(self, delete, update, session):
        update.return_value = "update"
        delete.return_value = "delete"
        permissions_criterion_mock = mock.MagicMock()

        class BulkAction(Permed):
            @classmethod
            def permissions_criterion(cls, *args, **kwargs):
                permissions_criterion_mock(*args, **kwargs)
                return and_(True)

        query = session.query(BulkAction)
        assert query.update({"foo": "bar"}) == "update", "bulk update calls underyling update"
        permissions_criterion_mock.assert_called_with("update")
        update.assert_called_with({"foo": "bar"})

        assert query.delete() == "delete", "bulk delete calls underyling update"
        permissions_criterion_mock.assert_called_with("delete")
        delete.assert_called_with(), "delete called"

def test__Model_contract():
    class ConcreteModel(orm.Model):
        __tablename__ = "concrete_model"

    assert isinstance(ConcreteModel.id, InstrumentedAttribute), "id is a column"
    assert isinstance(ConcreteModel.id.type, UUIDType), "id is a uuid"
