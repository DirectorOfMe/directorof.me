import uuid
import datetime

from directorofme_event.models import Event, EventType
from directorofme.testing import commit_with_integrity_error, existing


class TestEventType:
    def test__mininum_well_formed(self, db, disable_permissions):
        event_type = EventType(name="test", desc="test event_type")
        assert event_type.name == "test", "name set"
        assert event_type.slug == "test", "slug generated from name by __init__"
        assert event_type.desc == "test event_type", "description (desc) set"

        assert event_type.id is None, "id None until saved"
        assert existing(event_type, "name") is None, "no event_type pre-save"

        db.session.add(event_type)
        db.session.commit()

        assert isinstance(event_type.id, uuid.UUID), "id set after commit"
        assert existing(event_type, "name").id == event_type.id, "event_type in DB"


    def test__unique_name_and_slug(self, db, disable_permissions):
        event_type = EventType(name="foo", desc="r")
        assert existing(event_type, "name") is None, "event_type not saved"

        db.session.add(event_type)
        db.session.commit()
        assert existing(event_type, "name").id == event_type.id, "event_type in DB"

        event_type_duplicate_name = EventType(name="foo", desc="r")
        event_type_duplicate_name.slug = "uniq"
        assert existing(event_type_duplicate_name, "slug") is None, "slug is unique"
        commit_with_integrity_error(db, event_type_duplicate_name)

        event_type_duplicate_slug = EventType(name="uniq", desc="r")
        event_type_duplicate_slug.slug = "foo"
        assert existing(event_type_duplicate_slug, "name") is None, "name is unique"
        commit_with_integrity_error(db, event_type_duplicate_slug)

    def test__required_fields(self, db, disable_permissions):
        missing_name = EventType(slug="foo", desc="r")
        assert existing(missing_name, "slug") is None, "slug is unique"
        commit_with_integrity_error(db, missing_name)

        missing_slug = EventType(name="foo", desc="r")
        missing_slug.slug = None
        assert existing(missing_slug, "name") is None, "name is unique"
        commit_with_integrity_error(db, missing_slug)

        missing_desc = EventType(name="foo")
        assert missing_desc.slug is not None, "slug set"
        assert existing(missing_desc, "name") is None, "name is unique"
        assert existing(missing_desc, "slug") is None, "slug is unique"
        commit_with_integrity_error(db, missing_desc)


class TestEvent:
    def test__mininum_well_formed(self, db, disable_permissions):
        event_type = EventType(name="test", desc="test event_type")
        assert existing(event_type, "name") is None, "no event_type pre-save"

        event = Event(event_type=event_type)
        assert event.event_type == event_type, "event_type setup correctly"
        assert event.event_type_id is None, "event_type_id is None until saved"
        assert event.id is None, "id None until saved"
        assert event.cursor is None, "cursor is None until saved"
        assert event.event_type_slug == event_type.slug, "event_type_slug property works"

        db.session.add(event)
        db.session.commit()

        assert isinstance(event.id, uuid.UUID), "id set after commit"
        assert isinstance(event_type.id, uuid.UUID), "id set after commit"

        assert existing(event_type).id == event_type.id, "event_type in DB"
        assert existing(event).id == event.id, "event in DB"
        assert isinstance(existing(event).cursor, int), "cursor is an integer after save"
        assert isinstance(existing(event).event_time, datetime.datetime), "event_time is a date at save"


    def test__required_fields(self, db, disable_permissions):
        missing_event_type = Event(event_time=datetime.datetime.now())
        commit_with_integrity_error(db, missing_event_type)

        event = Event(event_type=EventType(name="test", desc="test event_type"))
        db.session.add(event)
        db.session.commit()

        event.event_time = None
        commit_with_integrity_error(db, event)

        event.event_time = datetime.datetime.now()
        db.session.add(event)
        db.session.commit()

        cursor = event.cursor
        event.cursor = None
        commit_with_integrity_error(db, event)

        event.cursor = cursor
        db.session.add(event)
        db.session.commit()
