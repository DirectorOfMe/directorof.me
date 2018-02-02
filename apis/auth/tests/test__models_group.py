import uuid
from directorofme_auth.models import Group, GroupTypes

class TestGroup:
    def test__mininum_well_formed(self, db):
        group = Group(display_name="test", type=GroupTypes.feature)
        assert group.display_name == "test", "display_name set"
        assert group.type == GroupTypes.feature, "type set"
        assert group.name == "f-test", "name auto-set from display_name and type"
        assert group.id is None

        db.session.add(group)
        db.session.commit()

        assert isinstance(group.id, uuid.UUID), "id set after commit"

    def test__name_auto_generates_when_display_name_and_type_set(self, db):
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

    def test__parent_():
