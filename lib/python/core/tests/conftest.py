import os
import pytest
import flask

from unittest import mock

from flask.sessions import SessionInterface

from directorofme.authorization import groups, session

### COPIED FROM FLASK ITSELF
@pytest.fixture
def app():
    app = flask.Flask('flask_test', root_path=os.path.dirname(__file__))
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
