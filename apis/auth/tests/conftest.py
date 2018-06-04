import pytest

from directorofme_auth import db as real_db, app
from directorofme.testing import db as db
from directorofme_auth.models import Group, Profile, App, InstalledApp
from directorofme.authorization import groups

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
    with real_db.Model.disable_permissions():
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
    installed_app = app.install_for_group(profile.group_of_one)

    db.session.add_all(scope_groups)
    db.session.add(app)
    db.session.add(profile)
    db.session.add(installed_app)
    db.session.commit()

    yield profile

@pytest.fixture
def private_key():
    return """-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCice5T7hT6WWRW4mD5w4HtWXgLq5hHlzqjfVB5ZCazjWRVH68J
gOYybPEM0DXwfYc+QNqVYHkPOPnmgXce/KMdRx/jAnDulLqbM+kv1Gcj+bMUNDd6
2FNlKeucQe3YxAHN1GqLC94/imjIhJIU8ZlPNUTD5M61fZCF9uBHosRHDwIDAQAB
AoGAGVtbbnJ9h86oYP+ZT6N7Boeuu3Ofo50xpA+NnkVJ3UE25iq58evTAxAKWIuv
v8h4cflBpYuXmg60w4x2AbpB47InSS+CchWRUSv/HAGmF2Vnm7fH10PvPEvJt9Rx
T+Q+zMdWRz4oxHHf2ni1wtZ/mnA/RIEOyXI7hok+W1NtdMECQQC6P5YrUMrhxfYF
bX3PiCqMl8tPaVTQJjJ+ZsegmziXRJfL5FH9kt/NQ4gAzYD1LOelkhibJKp+R3Cj
lExQTZp/AkEA30g32ZZQpIGqGoGzgGOgs8AeHgWtODYAMfMl2wAjA3tFZRaZcGPV
MAAOmhV35vECt3Gv1YS+cmxy2PR7ZxBrcQJAYuxNHZqe98YGgyGBtk3zk5M4SGiA
xMHVBfAfTb3EFAw5t/EAX3e4aTTaMtr0CMUeEIIFkbmq2MGnISsuUWS2jwJBAIDG
wB9oSF54wkjDYWm9DCRfu38JOxxeWMJ2P/ENJSSO5jklTZ26lmw2vDU2CI9TlYOD
uCvngYew8JQcfUe1+qECQGmyAmfpHaAiyc8DvwAa35qwIKoGXwr/chOoz33L9I6E
AArvfT8Gst6rfbb404/QqqFMZhSVTUpE6o4jbfCYc/4=
-----END RSA PRIVATE KEY-----"""

@pytest.fixture
def public_key():
    return """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCice5T7hT6WWRW4mD5w4HtWXgL
q5hHlzqjfVB5ZCazjWRVH68JgOYybPEM0DXwfYc+QNqVYHkPOPnmgXce/KMdRx/j
AnDulLqbM+kv1Gcj+bMUNDd62FNlKeucQe3YxAHN1GqLC94/imjIhJIU8ZlPNUTD
5M61fZCF9uBHosRHDwIDAQAB
-----END PUBLIC KEY-----"""
