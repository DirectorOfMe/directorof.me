import pytest

from directorofme_event import db as real_db
from directorofme.testing import DBFixture, disable_permissions

# setup the db fixture
# TODO: autouse?
db = pytest.fixture(autouse=True)(DBFixture(real_db).fixture())
disable_permissions = pytest.fixture(disable_permissions)
