import pytest

from directorofme_event import db as real_db
from directorofme.testing import DBFixture

# setup the db fixture
# TODO: autouse?
db = pytest.fixture(autouse=True)(DBFixture(real_db).fixture())
