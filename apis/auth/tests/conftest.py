import pytest

from directorofme_auth import db as real_db, app
from directorofme.testing import db as db
from directorofme_auth.models import Group, Profile, App, InstalledApp
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
def disable_permissions(request_context):
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
    scope_groups = Group.create_scope_groups(groups.Scope(display_name="main"))
    app = App(name="main", requested_access_groups=scope_groups, desc="main app", url="https://example.com/")
    profile = Profile.create_profile("test", "test@example.com")
    installed_app = InstalledApp.install_for_group(app, profile.group_of_one)

    db.session.add_all(scope_groups)
    db.session.add(app)
    db.session.add(profile)
    db.session.add(installed_app)
    db.session.commit()

    yield profile
