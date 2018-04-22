import pytest

from directorofme_event import db as real_db
from directorofme.authorization.orm import Model
from directorofme.testing import db

# setup the db fixture
# TODO: autouse?
db = pytest.fixture(autouse=True)(db(real_db))

@pytest.fixture
def disable_permissions():
    with Model.disable_permissions():
        yield
