import os
import pytest
import flask
import flask_restful

### COPIED FROM FLASK ITSELF
@pytest.fixture
def app():
    app = flask.Flask('flask_test', root_path=os.path.dirname(__file__))
    return app

@pytest.fixture
def api(app):
    return flask_restful.Api(app)
