import pytest

from directorofme_event import db as real_db
from directorofme.authorization.orm import disable_permissions
from directorofme.testing import db

# setup the db fixture
# TODO: autouse? 
db = pytest.fixture(autouse=True)(db(real_db))
disable_permissions = pytest.fixture(disable_permissions)
