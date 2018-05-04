import pytest
import flask

from unittest import mock

from directorofme.authorization import groups
from directorofme.flask import Model, DOMSQLAlchemy

def test__Model(request_context_with_session):
    assert Model.load_groups() == [groups.everybody], "load_groups loads gruops from the flask session"
    with mock.patch.object(flask.session, "default_object_perms", { "read": (groups.everybody,) }):
        assert Model.default_perms("read") == (groups.everybody,), \
               "default_perms loads groups from the flask session"

def test__DOMSQLAlchemy():
    test_app = flask.Flask("test")
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite3:///"
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    for obj in (DOMSQLAlchemy(scope_name="test"), DOMSQLAlchemy(test_app)):
        assert obj.Model.__tablename_prefix__ == "test", "prefix set"
        assert obj.Model.__scope__.read.name == "s-test-read", "scope setup"
        assert obj.Model is not Model, "Model is not mutated"
        assert issubclass(obj.Model, Model), "appless Model inherits Base Model"

    with pytest.raises(ValueError):
        DOMSQLAlchemy()
