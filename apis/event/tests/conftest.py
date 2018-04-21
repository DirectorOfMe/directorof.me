import pytest

from directorofme_event import db as real_db
from directorofme.authorization.orm import disable_permissions as disable_permissions_decorator
from directorofme.testing import db

# setup the db fixture
# TODO: autouse?
db = pytest.fixture(autouse=True)(db(real_db))

@pytest.fixture
def disable_permissions():
    with disable_permissions_decorator():
        yield
