import pytest
import json

from directorofme.json import JSONEncoder
from directorofme.authorization import standard_permissions
from directorofme.authorization.groups import GroupTypes, Group, Scope, scope, root, admin, nobody, \
                                              everybody, user, staff, base_groups

class TestGroupTypes:
    def test__GroupTypes_spec(self):
        for kk, vv in {"system": "0", "scope": "s", "feature": "f", "data": "d"}.items():
            assert getattr(GroupTypes, kk).value == vv, "scope prefix is correct"

    def test__GroupTypes_spec(self):
        for name in ("system", "scope", "feature", "data"):
            assert json.loads(json.dumps(getattr(GroupTypes, name), cls=JSONEncoder)) == name, "json encoding"

class TestGroup:
    def test__init__(self):
        group = Group(name="0-sYstem", display_name="System", type=GroupTypes.system)

        assert group.name == "0-sYstem", "passed name set correctly"
        assert group.display_name == "System", "passed display_name set correctly"
        assert group.type == GroupTypes.system, "passed type set correctly"

        with pytest.raises(ValueError):
            # should raise if display_name or name is not passed
            Group(type=GroupTypes.system)

        with pytest.raises(ValueError):
            # should raise if type or name not passed
            Group(display_name="hahahaha")

        assert Group(name="hahahhaha").name == "hahahhaha", "only passing name works"

        gen_name = Group(display_name="root", type=GroupTypes.system)
        assert isinstance(gen_name, Group), "display name and type passed works"
        assert isinstance(gen_name.name, str), "str name generated if not passed"

    def test__generate_name_happy_path(self):
        group = Group(display_name="root", type=GroupTypes.system)

        assert group.name == "0-root", "init defaulted"

        group.name = "manual"
        assert group.generate_name() == "manual", "name returned if set"

        group.name = None
        assert group.generate_name() == "0-root", "name generated if not set"
        assert group.name is None, "no side-effects"

        group.display_name = "I Am A Sentence"
        group.type = GroupTypes.scope
        assert group.generate_name() == "s-i-am-a-sentence", "name is slugged"
        assert group.name is None, "no side-effects"

    @pytest.mark.parametrize("kwargs", [
        { "display_name": "root" },                          # missing type
        { "type": GroupTypes.system },                       # missing display_name
        { "type": None, "display_name": "root" },            # type is None
        { "type": GroupTypes.system, "display_name": None},  # display_name is None
        { "type": GroupTypes.system, "display_name": True }, # display_name not a str
        { "type": "this one", "display_name": "root"},       # type is not a GroupType
    ])
    def test__generate_name_errors(self, kwargs):
        with pytest.raises(ValueError):
            # test uninitialized type raises
            Group(**kwargs)

    def test__str__(self):
        group = Group(display_name="foo", type=GroupTypes.system)
        assert str(group) == group.name, "str works"

    def test__hash__(self):
        group = Group(display_name="foo", type=GroupTypes.system)
        assert group.__hash__() == hash(group.name), "hash function returns name"
        assert group in {group}, "works with sets & dicts"

    def test__eq___and___ne__(self):
        group = Group(display_name="foo", type=GroupTypes.system)
        group2 = Group(display_name="foo", type=GroupTypes.system)
        other = Group(display_name="bar", type=GroupTypes.system)

        assert group is not group2, "instances are different"
        assert group == group2, "instances are equivalent"
        assert not group == other, "different names are not equivalent"
        assert group != other, "different names are !="

        assert group.__eq__(object()) is NotImplemented, "__eq__ against object isn't implemented"
        assert group.__ne__(object()) is NotImplemented, "__ne__ against object isn't implemented"

class TestScope:
    def test__init__(self):
        test = Scope(name="tEst", display_name="test", __perms__=("test",))
        assert test.name == "tEst", "passed name set correctly"
        assert test.display_name == "test", "passed display_name set correctly"
        assert test.__perms__ == ("test",), "passed __perms__ set correctly"
        assert isinstance(test.perms["test"], Group), "__perms__ builds permissions"

        assert test.perms["test"].display_name == test.perm_name("test"), \
               "display name of group set correctly"
        assert test.perms["test"].type == GroupTypes.scope, "perm GroupType is scope"

        test_perm = Scope(name="tEst", display_name="test", perms=test.perms)
        assert test_perm.perms == test.perms, "passing perms works"
        assert test_perm.__perms__ == test.__perms__, "perms generates __perms__"

        with pytest.raises(ValueError):
            # if neither display_name or name provided, should error
            Scope()

        Scope(name="test").name == "test", "only passing name works"

        gen_name = Scope(display_name="Test It")
        assert isinstance(gen_name, Scope), "display name and type passed works"
        assert isinstance(gen_name.name, str), "str name generated if not passed"
        assert set(Scope(name="test").perms.keys()) == set(standard_permissions), \
               "perms default to standard"

    def test__getattr__(self):
        test = Scope(name="test", __perms__=("test",))

        assert isinstance(test.perms["test"], Group), "test perm installed"
        assert isinstance(test.test, Group), "test accessible via `.`"

        with pytest.raises(AttributeError):
            test.read

    def test__generate_name(self):
        scope_ = Scope(display_name="test")

        assert scope_.name == "test", "init defaulted"

        scope_.name = "manual"
        assert scope_.generate_name() == "manual", "name returned if set"

        scope_.name = None
        assert scope_.generate_name() == "test", "name generated if not set"
        assert scope_.name is None, "no side-effects"

        scope_.display_name = "I Am A Sentence"
        assert scope_.generate_name() == "i-am-a-sentence", "name is slugged"
        assert scope_.name is None, "no side-effects"

    def test__perm_name(self):
        scope_ = Scope(name="test", __perms__=("test",))
        assert scope_.perm_name("test") == "test-test", \
               "permission name combines permission name and scope name"

        scope_ = Scope(name="Test It", __perms__=("Test It",))
        assert scope_.perm_name("Test It") == "test-it-test-it", "name is slugged"

    def test__merge(self):
        one = Scope(name="test", __perms__=("one",))
        two = Scope(name="test", __perms__=("two",))

        merged = one.merge(two)
        assert sorted(merged.__perms__) == ["one", "two"], "both sets of permissions present"
        assert merged.perms["one"] is one.perms["one"], "permission one is correct"
        assert merged.perms["two"] is two.perms["two"], "permission two is correct"

        assert merged is not one, "new object returned"
        assert merged is not two, "nwe object returned"

        merged = Scope(name="test", __perms__=("one",)).merge(one)
        assert tuple(merged.perms.keys()) == ("one",), "only one perm after merge"
        assert merged.perms["one"] is one.perms["one"], \
               "when both sides have a perm, right side over-rides left"

        mismatched_one = Scope(name="test")
        mismatched_two = Scope(name="nope")
        with pytest.raises(ValueError):
            mismatched_one.merge(mismatched_two)

        display_named_one = Scope(name="test", display_name="one")
        display_named_two = Scope(name="test", display_name="two")

        assert display_named_one.merge(Scope(name="test")).display_name == "one", \
               "take left-side display name if only left-side is set"
        assert Scope(name="test").merge(display_named_two).display_name == "two", \
               "take right-side display name if only right-side is set"
        assert display_named_one.merge(display_named_two).display_name == "two", \
               "take right-side display name if both are set"

class Foo:
    pass

def test__scope_called_with_string():
    assert "hi" not in scope.known_scopes
    assert callable(scope("hi")), "scope with a name should return a decorator"
    assert 'hi' in scope.known_scopes, "scope `hi` registered with known_scopes"

    assert isinstance(scope.known_scopes["hi"], Scope), "`hi` is a scope"
    assert scope.known_scopes["hi"].name == "hi", "`hi` Scope is named `hi`"

    scope("foo")
    foo_scope = scope.known_scopes["foo"]
    assert scope("foo")(Foo) is Foo, "decorator returns class in tact"
    assert scope.known_scopes["foo"] is foo_scope, \
           "initial registration not overwritten by subsequent registration"

class Bar:
    pass

class Modelish:
    __tablename__ = "model"

def test__scope_called_with_class():
    assert "bar" not in scope.known_scopes
    assert scope(Bar) is Bar, "scope called with class should return the class"
    assert "bar" in scope.known_scopes, "scope registration by class name works"

    assert "model" not in scope.known_scopes
    assert scope(Modelish) is Modelish, \
           "scope called with model class shouldreturn the class"
    assert "model" in scope.known_scopes, \
           "class registration by __tablename__ attribute works"


def test__base_groups():
    assert set(base_groups) == {root, admin, nobody, everybody, user, staff}, "base groups has all base groups"
    assert root.name == "0-root", "root name is correct"
    assert admin.name == "0-admin", "admin name is correct"
    assert nobody.name == "0-nobody", "admin name is correct"
    assert everybody.name == "0-everybody", "admin name is correct"
    assert user.name == "f-user", "admin name is correct"
    assert staff.name == "f-staff", "staff name is correct"
