import os
import pytest
import flask

from unittest import mock

### COPIED FROM FLASK ITSELF
@pytest.fixture
def app():
    app = flask.Flask('flask_test', root_path=os.path.dirname(__file__))
    return app

@pytest.fixture
def clear_env():
    with mock.patch.dict(os.environ, {}, clear=True):
        yield
