import uuid

import pytest

from directorofme.testing import existing, commit_with_integrity_error
from directorofme.authorization import groups

from directorofme_auth.models import Profile, Group, GroupTypes, License
from directorofme_auth.models.exceptions import NoProfileError, MissingGroupError

class TestProfile:
    def test__mininum_well_formed(self, db, disable_permissions):
        id_ = uuid.uuid1()
        group = Group(display_name=id_.hex, type=GroupTypes.data)
        profile = Profile(id=id_, name="test", email="test@example.com", group_of_one=group)
        assert profile.id == id_, "id sets correctly"
        assert profile.name == "test" , "name sets correctly"
        assert profile.email == "test@example.com", "email sets correctly"
        assert profile.group_of_one is group, "group_of_one sets correctly"

        assert existing(profile) is None, "no profile already exists"
        db.session.add(profile)
        db.session.commit()

        assert existing(profile).id == id_, "profile saved to DB"

    def test__init__(self, db, disable_permissions):
        id_ = uuid.uuid1()
        assert Profile(id=id_).id == id_, "can instantiate with id"

        with pytest.raises(NoProfileError):
            Profile()

    def test__required_fields(self, db, disable_permissions):
        id_ = uuid.uuid1()
        group = Group(display_name=id_.hex, type=GroupTypes.data)

        # name
        missing_name = Profile(id=id_, email="test@example.com", group_of_one=group)
        assert existing(missing_name, "email") is None, "profile doesn't exist"
        commit_with_integrity_error(db, missing_name)

        missing_name.name = "Foo Bar"
        db.session.add(missing_name)
        db.session.commit()
        assert existing(missing_name, "email").name == "Foo Bar", \
               "save works if name set"

        # email
        id_ = uuid.uuid1()
        group = Group(display_name=id_.hex, type=GroupTypes.data)
        missing_email = Profile(id=id_, name="Foo Bar", group_of_one=group)
        assert existing(missing_email) is None, "profile doesn't exist"
        commit_with_integrity_error(db, missing_email)

        missing_email.email= "test1@example.com"
        db.session.add(missing_email)
        db.session.commit()
        assert existing(missing_email, "email").email== "test1@example.com",\
               "save works if email set"

        # group_of_one
        id_ = uuid.uuid1()
        missing_group = Profile(id=id_, name="FB", email="test2@example.com")
        assert existing(missing_group, "email") is None, "profile doesn't exist"
        commit_with_integrity_error(db, missing_group)

        group = Group(display_name=id_.hex, type=GroupTypes.data)
        missing_group.group_of_one = group
        db.session.add(missing_group)
        db.session.commit()
        assert existing(missing_group, "email").email== "test2@example.com",\
               "save works if group set"

    def test__create_profile(self, db, disable_permissions, user_group):
        profile = Profile.create_profile("Test", "test@example.com")
        assert isinstance(profile.id, uuid.UUID), "uuid is set"
        assert profile.group_of_one.type == GroupTypes.data, "group_of_one is data"
        assert profile.group_of_one.display_name == profile.id.hex, \
               "group_of_one is id"
        assert profile.group_of_one.name in profile.group_of_one.read, \
               "group_of_one has read permission to itself"

        db.session.add(profile)
        db.session.commit()

        license = License.query.filter(License.managing_group == profile.group_of_one).first()
        assert set(license.groups) == {
            profile.group_of_one, Group.query.filter(Group.name == groups.user.name).first()
        }, "license has group_of_one as the member group"
        assert list(license.profiles) == [profile], "license lists"

        profile = Profile.create_profile("Test", "test@a.com", additional_groups=[
                        Group(display_name="foo", type=GroupTypes.data)
                  ], add_user_group=False)

        groups_list = list(profile.licenses.first().groups)
        assert len(groups_list)== 2, "two groups installed when additional group passed"
        assert groups_list[0].id == profile.group_of_one_id
        assert groups_list[1].name == "d-foo"

    def test__create_profile_without_user_group(self, db, disable_permissions):
        with pytest.raises(MissingGroupError):
            Profile.create_profile("Test", "test@example.com")

        profile = Profile.create_profile("Test", "test@example.com", add_user_group=False)
        assert profile.email == "test@example.com", "profile is created with flag"

