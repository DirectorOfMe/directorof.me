import pytest

from directorofme_auth import db as real_db, app
from directorofme.testing import DBFixture

# setup the db fixture
# TODO: autouse?
db = pytest.fixture(autouse=True)(DBFixture(real_db).fixture())

@pytest.fixture
def request_context():
    with app.test_request_context() as ctx:
        yield ctx

@pytest.fixture
def test_client():
    with app.test_client() as client:
        yield client
