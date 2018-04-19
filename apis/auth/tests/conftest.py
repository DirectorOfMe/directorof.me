import pytest
import uuid
import requests

from directorofme_auth import db as real_db, app
from directorofme_auth.models import Group, GroupTypes, Profile
from directorofme.testing import DBFixture, disable_permissions
from directorofme.authorization.orm import Model

# setup the db fixture
# TODO: autouse?
db = pytest.fixture(autouse=True)(DBFixture(real_db).fixture())

@pytest.fixture
def test_profile(db):
    id_ = uuid.uuid1()
    group = Group(display_name=id_.hex, type=GroupTypes.data)
    profile = Profile.create_profile("test", "test@example.com")

    db.session.add(profile)
    db.session.commit()
    yield profile

@pytest.fixture
def request_context():
    with app.test_request_context() as ctx:
        yield ctx

@pytest.fixture
def test_client():
    with app.test_client() as client:
        yield client

disable_permissions = pytest.fixture(disable_permissions)
