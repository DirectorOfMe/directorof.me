import os
import pytest
import flask

from unittest import mock

from flask.sessions import SessionInterface
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from directorofme.authorization import groups, session, orm
from directorofme.flask.json import JSONEncoder

### COPIED FROM FLASK ITSELF
@pytest.fixture
def app():
    app = flask.Flask('flask_test', root_path=os.path.dirname(__file__))
    app.json_encoder = JSONEncoder
    return app

@pytest.fixture
def clear_env():
    with mock.patch.dict(os.environ, {}, clear=True):
        yield

class TestSessionInterface(SessionInterface):
    def open_session(self, *args):
        return session.Session(save=False, app=None, profile=None, groups=[groups.everybody],
                               environment={}, default_object_perms={})

@pytest.fixture
def request_context_with_session(app):
    app.session_interface = TestSessionInterface()
    with app.test_request_context() as ctx:
        yield ctx

@pytest.fixture
def engine():
    return create_engine('sqlite://')

@pytest.fixture
def Session():
    return sessionmaker(query_cls=orm.PermissionedQuery)

@pytest.fixture
def bound_session(Session, engine):
    return Session(bind=engine)
