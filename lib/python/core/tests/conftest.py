import os
import pytest
import flask

### COPIED FROM FLASK ITSELF
@pytest.fixture
def app():
    app = flask.Flask('flask_test', root_path=os.path.dirname(__file__))
    return app
