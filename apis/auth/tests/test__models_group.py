import uuid

from directorofme.authorization.groups import Scope, Group as AuthGroup
from directorofme.testing import existing, commit_with_integrity_error

from directorofme_auth.models import Group, GroupTypes

class TestGroup:
    def test__mininum_well_formed(self, db, disable_permissions):
        group = Group(display_name="test", type=GroupTypes.feature)
        assert group.display_name == "test", "display_name set"
        assert group.type == GroupTypes.feature, "type set"
        assert group.name == "f-test", "name auto-set from display_name and type"
        assert group.id is None

        db.session.add(group)
        db.session.commit()

        assert isinstance(group.id, uuid.UUID), "id set after commit"

    def test__name_auto_generates_when_display_name_and_type_set(self, db, disable_permissions):
        incomplete = Group()
        assert incomplete.name is None, "name is none when neither is set"

        incomplete.display_name = "hi"
        assert incomplete.name is None, "name is none when only display_name is set"

        incomplete.type = GroupTypes.system
        assert incomplete.name == "0-hi", "name auto-set when type is set"

        incomplete_two = Group(type=GroupTypes.scope)
        assert incomplete_two.name is None, "name is none when only type is set"

        incomplete_two.display_name = "hi"
        assert incomplete_two.name == "s-hi", "name auto-set when display_name is set"

        named = Group(name="different", display_name="nope", type=GroupTypes.scope)
        assert named.name == "different", "name not overridden when passed to init"

        named_two = Group(name="different-two")
        assert named_two.name == "different-two", "passed name is OK"

        named_two.display_name = "nope"
        named_two.type = GroupTypes.feature
        assert named_two.name == "different-two", "observer doesn't change name"

    def test__unique_name(self, db, disable_permissions):
        assert Group.query.filter(Group.name == "name").first() is None, \
               "no group with name name"

        db.session.add(Group(name="name", display_name="hi", type=GroupTypes.system))
        db.session.commit()
        assert isinstance(Group.query.filter(Group.name == "name").first(), Group), \
               "object successfully saved"

        db.session.add(Group(name="name", display_name="no", type=GroupTypes.data))
        commit_with_integrity_error(db)

    def test__unique_display_name_and_type(self, db, disable_permissions):
        assert Group.query.filter(Group.name == "uniq").first() is None, \
               "uniq group does not exist"
        assert Group.query.filter(
            (Group.display_name == "test") & (Group.type == GroupTypes.data)
        ).first() is None, "d-test doesn't exist"

        db.session.add(Group(name="uniq", display_name="test", type=GroupTypes.data))
        db.session.commit()
        assert isinstance(Group.query.filter(
            (Group.display_name == "test") & (Group.type == GroupTypes.data)
        ).first(), Group), "group with type data and display_name test exists"

        assert Group.query.filter(Group.name == "uniq2").first() is None, \
               "uniq2 group does not exist"
        db.session.add(Group(name="uniq2", display_name="test", type=GroupTypes.data))
        commit_with_integrity_error(db)

    def test__required_fields(self, db, disable_permissions):
        # missing type
        commit_with_integrity_error(db, Group(name="hi", display_name="hi"))

        db.session.rollback()
        commit_with_integrity_error(db, Group(name="hi", type=GroupTypes.data))

        nameless = Group(display_name="hi", type=GroupTypes.data)
        nameless.name = None
        commit_with_integrity_error(db, nameless)

    def test__members_and_members_of(self, db, disable_permissions):
        assert Group.query.filter(
            Group.display_name.like("child-%")
        ).first() is None, "no children in DB"

        parent = Group(display_name="parent", type=GroupTypes.data)
        db.session.add(parent)
        for i in range(5):
            parent.members.append(
                Group(display_name="child-{}".format(i), type=GroupTypes.data)
            )
        db.session.commit()

        children = []
        parent2 = Group(display_name = "parent2", type=GroupTypes.data)
        for child in Group.query.filter(Group.display_name.like("child-%")):
            assert child.member_of == [parent]
            child.member_of.append(parent2)
            db.session.add(child)
            children.append(child)

        assert parent.members == children, "all children were added"
        db.session.commit()
        assert parent2.members == parent.members, "setting parent on child works"

    def test__slugify_name(self, db, disable_permissions):
        group = Group()
        assert group.slugify_name() is None, "nothing set, nothign passed is None"

        group.name = "hi"
        assert group.slugify_name() == "hi", "name set, nothing passed is `name`"

        assert group.slugify_name(type=GroupTypes.data) == "hi", \
               "name set, type passed is still name"
        assert group.slugify_name(display_name="foo") == "hi", \
               "name set, display_name passed is still name"
        assert group.slugify_name(display_name="foo", type=GroupTypes.data) == "hi", \
               "name set, display_name and type passed is still name"

        group.display_name = "foo"
        assert group.slugify_name() == "hi", "name and display_name set, returns name"
        group.display_name = None
        group.type = GroupTypes.data
        assert group.slugify_name() == "hi", "name and type set, returns name"
        group.display_name = "foo"
        assert group.slugify_name() == "hi", \
               "name and display_name and type set, returns name"

        group.name = None
        assert group.slugify_name() == "d-foo", "display_name and type set generates"
        assert group.name is None, "no side-effects"
        assert group.slugify_name(type=GroupTypes.system) == "0-foo", \
               "passed type overrides set type"
        assert group.name is None, "no side-effects"
        assert group.type is GroupTypes.data, "no side-effects"

        assert group.slugify_name(display_name="hello") == "d-hello", \
               "passed display_name overrides set type"
        assert group.name is None, "no side-effects"
        assert group.display_name == "foo", "no side-effects"

    def test__scope(self, db, disable_permissions):
        scoped = Group(display_name="not_scoped", type=GroupTypes.data)
        assert scoped.scope() is None, "missing scope & scope_perimssion returns None"

        scoped.scope_name = "no_perm"
        assert scoped.scope() is None, "missing scope_perimssion returns None"

        scoped.scope_name = None
        scoped.scope_permission = "test"
        assert scoped.scope() is None, "missing scope returns None"

        scoped.scope_name = "test"
        scope_ = scoped.scope()
        assert isinstance(scope_, Scope), "has name and permission returns scope"
        assert scope_.name == "test", "scope_name set properly"
        assert isinstance(scope_.perms["test"], AuthGroup), "group installed"
        assert scope_.perms["test"].name == scoped.name, "group installed"


    def test__scopes(self, db, disable_permissions):
        assert Group.scopes([]) == [], "empty groups list returns empty scopes list"
        assert Group.scopes([Group(display_name="dom", type=GroupTypes.data)]) == [],\
               "Groups with no scope returns empty list"

        scope_one_groups = [
            Group(display_name="foo", type=GroupTypes.data,
                  scope_name="one", scope_permission="read"),
            Group(display_name="bar", type=GroupTypes.data,
                  scope_name="one", scope_permission="write")
        ]

        assert len(Group.scopes(scope_one_groups)) == 1, \
               "many groups in one scope return only one scope"

        scope_one = Group.scopes(scope_one_groups)[0]
        assert scope_one.name == "one", "scope_one has the correct name"
        assert sorted(scope_one.__perms__) == [ "read", "write" ], \
               "scope_one has the correct perm names"
        for perm, group in (("read", scope_one_groups[0]),
                            ("write", scope_one_groups[1])):
            assert scope_one.perms[perm].name == group.name, "groups installed"

        two_scopes_groups = scope_one_groups + [
            Group(display_name="baz", type=GroupTypes.data,
                  scope_name="two", scope_permission="test"),
            Group(display_name="bang", type=GroupTypes.data,
                  scope_name="two", scope_permission="this")
        ]
        two_scopes = sorted(Group.scopes(two_scopes_groups), key=lambda x: x.name)

        assert len(two_scopes) == 2, "two scopes from the 4 passed groups"
        assert two_scopes[0].name == "one", "scope one set correctly"
        assert sorted(two_scopes[0].__perms__) == [ "read", "write" ], \
               "scopes[0] has the correct perm names"

        assert two_scopes[1].name == "two", "scope two set correctly"
        assert sorted(two_scopes[1].__perms__) == [ "test", "this" ], \
               "scopes[1] has the correct perm names"

        for perm, group in (("test", two_scopes_groups[2]),
                            ("this", two_scopes_groups[3])):
            assert two_scopes[1].perms[perm].name == group.name, "groups installed"

    def test__expand(self, db, disable_permissions):
        dom = Group(display_name="dom", type=GroupTypes.data)
        dom_employees = Group(display_name="dom-emp", type=GroupTypes.data)
        dom_employees.member_of = [dom]
        assert existing(dom, "name") is None, "dom group not installed"
        assert existing(dom_employees, "name") is None, "dom_employees not installed"

        prog = Group(display_name="programmers", type=GroupTypes.data)
        dom_prog = Group(display_name="dom-programmers", type=GroupTypes.data)
        dom_prog.member_of = [dom_employees, prog]
        assert existing(prog, "name") is None, "dom group not installed"
        assert existing(dom_prog, "name") is None, "dom_employees group not installed"

        db.session.add_all([dom, dom_employees, prog, dom_prog])
        db.session.commit()

        expanded = [dom, dom_employees, dom_prog, prog]
        assert list(dom_prog.expand().order_by(Group.name)) == expanded, \
               "expand recurses correctly"

        assert list(dom_prog.expand(max_depth=0)) == [], \
               "max_depth 0 restricts to no members"

        assert list(dom_prog.expand(max_depth=1)) == [dom_prog], \
               "max_depth 1 restricts to just self"

        expanded = [dom_employees, dom_prog, prog]
        assert list(dom_prog.expand(max_depth=2).order_by(Group.name)) == expanded, \
               "max_depth 2 restricts to self and parents"

    def test__expand_does_not_infinitely_recurse(self, db, disable_permissions):
        everybody = Group(display_name="everybody", type=GroupTypes.data)
        anybody = Group(display_name="anybody", type=GroupTypes.data)

        assert existing(everybody, "name") is None, "everybody not installed"
        assert existing(anybody, "name") is None, "everybody not installed"

        everybody.member_of = [anybody]
        anybody.member_of = [everybody]

        db.session.add_all([everybody, anybody])
        db.session.commit()

        assert list(everybody.expand().order_by(Group.name)) == [anybody, everybody],\
               "expand does not infinitely recurse when there are cycles"
        assert list(anybody.expand().order_by(Group.name)) == [anybody, everybody],\
               "expand does not infinitely recurse when there are cycles"

    def test__create_scope_groups(self, db, disable_permissions):
        scope_groups = Group.create_scope_groups(Scope(display_name="test-scope"))
        db.session.add_all(scope_groups)

        names, permissions = [], []
        for group in scope_groups:
            permissions.append(group.scope_permission)
            names.append(group.name)

            assert group.scope_name == "test-scope", "scope setup"
            assert group.type == GroupTypes.scope
            assert group.display_name == "test-scope-{}".format(permissions[-1]), \
                   "display name set correctly"
            assert group.name == "s-test-scope-{}".format(permissions[-1]), \
                   "test scope is named correctly"

        assert sorted(permissions) == ["delete", "read", "write"], \
               "default permissions are created by default"

        db.session.commit()
        assert sorted(names) == [i[0] for i in db.session.query(Group.name).filter(
            Group.scope_name == "test-scope"
        ).order_by(Group.name).all()], "objects can be retrieved by scope name"
