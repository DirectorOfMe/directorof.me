import pytest
import uuid
import requests

from directorofme_auth import db as real_db, app
from directorofme.testing import db as db
from directorofme_auth.models import Group, GroupTypes, Profile
from directorofme.authorization import groups
from directorofme.authorization.orm import Model

# setup the db fixture
# TODO: autouse?
db = pytest.fixture(autouse=True)(db(real_db))

@pytest.fixture
def request_context():
    with app.test_request_context() as ctx:
        yield ctx

@pytest.fixture
def test_client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def disable_permissions():
    with Model.disable_permissions():
        yield

@pytest.fixture
def user_group(disable_permissions, db):
    group = Group(display_name=groups.user.display_name, type=groups.user.type)
    db.session.add(group)
    db.session.commit()

    yield group

@pytest.fixture
def test_profile(db, user_group):
    id_ = uuid.uuid1()
    group = Group(display_name=id_.hex, type=GroupTypes.data)
    profile = Profile.create_profile("test", "test@example.com")

    db.session.add(profile)
    db.session.commit()

    yield profile
