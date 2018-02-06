import uuid

from directorofme.testing import existing, commit_with_integrity_error

from directorofme_auth.models import License, Group, GroupTypes, Profile

class TestModel:
    def test__mininum_well_formed(self, db):
        group = Group(display_name="test", type=GroupTypes.feature)
        license = License(managing_group=group, seats=1)

        assert license.managing_group is group, "group setup correctly"
        assert license.seats == 1, "seats installed correctly"
        assert license.notes is None, "notes hasn't defaulted yet"
        assert license.valid_through is None, "valid_through is None"

        db.session.add(license)
        db.session.commit()

        assert isinstance(license.id, uuid.UUID), "id set after commit"
        assert license.notes == "", "notes defaults to empty string"


    def test__required_fields(self, db):
        no_managing_group = License(seats=1)
        commit_with_integrity_error(db, no_managing_group)

        group = Group(display_name="test", type=GroupTypes.feature)
        no_managing_group.managing_group = group
        db.session.add(no_managing_group)
        db.session.commit()
        assert existing(no_managing_group).managing_group == group, \
               "save works if group set"

        no_seats = License(managing_group=group)
        commit_with_integrity_error(db, no_seats)

        no_seats.seats = 2
        db.session.add(no_seats)
        db.session.commit()
        assert existing(no_seats).seats == 2, "save works if seats set"

        # have to create, then update for notes due to default
        no_notes = License(managing_group=group, seats=2)
        db.session.add(no_notes)
        db.session.commit()

        no_notes.notes = None
        commit_with_integrity_error(db, no_notes)

        no_notes.notes = "hi"
        db.session.add(no_notes)
        db.session.commit()
        assert existing(no_notes).notes == "hi", "save works if notes set"

    def test__groups(self, db):
        mgmt = Group(display_name="test", type=GroupTypes.data)
        license = License(seats=2, managing_group=mgmt)

        groups = [ Group(display_name="pro", type=GroupTypes.feature),
                   Group(display_name="core", type=GroupTypes.feature) ]

        license.groups = groups

        db.session.add(license)
        db.session.commit()

        from_db = list(existing(license).groups)
        assert len(from_db) == 2, "2 groups saved"
        assert from_db[0].name == "f-pro", "group 1 corect"
        assert from_db[1].name == "f-core", "group 1 corect"


    def test__profiles_and_active_profiles(self, db):
        mgmt = Group(display_name="test", type=GroupTypes.data)
        license = License(seats=2, managing_group=mgmt)

        profiles = [
            Profile.create_profile("Tester 1", "test1@example.com"),
            Profile.create_profile("Tester 2", "test2@example.com"),
        ]

        license.profiles = profiles

        db.session.add(license)
        db.session.commit()

        from_db = existing(license)
        profiles = list(license.profiles)

        assert len(profiles) == 2, "two profiles"
        assert profiles[0].email == "test1@example.com", "profile 1 is correct"
        assert profiles[1].email == "test2@example.com", "profile 2 is correct"

        assert len(list(from_db.active_profiles)) == 2, "two profiles when seats is 2"
        from_db.seats = 1
        assert len(list(from_db.active_profiles)) == 1, "one profiles when seats is 1"
        from_db.seats = 0
        assert len(list(from_db.active_profiles)) == 0, "no profiles when seats is 0"
        from_db.seats = -1
        assert len(list(from_db.active_profiles)) == 2, "all profiles for -1 seats"
