import flask

from unittest import mock

from directorofme.authorization import groups
from directorofme.flask import Model

def test__Model(request_context_with_session):
    assert Model.load_groups() == [groups.everybody], "load_groups loads gruops from the flask session"
    with mock.patch.object(flask.session, "default_object_perms", { "read": (groups.everybody,) }):
        assert Model.default_perms("read") == (groups.everybody,), \
               "default_perms loads groups from the flask session"
