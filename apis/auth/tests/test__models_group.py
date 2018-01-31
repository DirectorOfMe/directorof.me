from sqlalchemy import event
import pytest

from directorofme_auth import db as real_db
from directorofme_auth.models import Group, GroupTypes

### TODO: move this to a shared lib
@event.listens_for(real_db.session, "before_commit")
def track_for_deletion(session):
    track_for_deletion.to_cleanup += list(session.new)
track_for_deletion.to_cleanup = []

@pytest.fixture
def db(request):
    yield real_db
    real_db.session.rollback()
    for obj in track_for_deletion.to_cleanup:
        real_db.session.delete(obj)

    real_db.session.commit()
    # reset track_for_deletion
    track_for_deletion.to_cleanup = []


class TestGroup:
    def test__test(self, db):
        db.session.add(Group(display_name="foo", type=GroupTypes.system))
        db.session.commit()

    def test__again(self, db):
        assert Group.query.filter(
                Group.display_name == "foo"
            ).filter(
                Group.type == GroupTypes.system
        ).first() is None, "teardown worked"
