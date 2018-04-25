import pytest
import uuid
import json

import flask

from unittest import mock

from directorofme.authorization.session import Session, SessionProfile, SessionApp, SessionDecorator, \
                                               do_with_groups, do_as_root
from directorofme.authorization import groups
from directorofme.json import JSONEncoder


### Tests
def test__SessionApp():
    assert SessionApp.attributes == {"id", "app_id", "app_name", "config"}, "attributes correct"

    app = SessionApp()
    assert isinstance(app, SessionApp), "init works with no args"

    app = SessionApp(id=uuid.uuid1(), app_id=uuid.uuid1(), app_name="test", config={})
    assert isinstance(app.id, uuid.UUID), "id set correctly by __init__"
    assert isinstance(app.app_id, uuid.UUID), "app_id set correctly by __init__"
    assert app.app_name == "test", "app_name set correctly by __init__"
    assert app.config == {}, "config set correctly by __init__"


def test__SessionProfile():
    assert SessionProfile.attributes == {"id", "email"}, "attributes correct"

    profile = SessionProfile()
    assert isinstance(profile, SessionProfile), "init works with no args"

    profile = SessionProfile(id=uuid.uuid1(), email="hi@example.com")
    assert isinstance(profile.id, uuid.UUID), "id set correctly by __init__"
    assert profile.email == "hi@example.com", "email set correctly by __init__"


class TestSession:
    def test__init__(self):
        assert Session.attributes == {"save", "app", "profile", "groups", "environment", "default_object_perms"},\
               "attributes correct"

        session = Session()
        assert isinstance(session, Session), "init works with no args"

        session = Session(save=True, app=SessionApp(), profile=SessionProfile(), groups=[],
                          environment={}, default_object_perms={})
        assert session.save == True, "save is set by __init__"
        assert isinstance(session.app, SessionApp), "app is set by __init__"
        assert isinstance(session.profile, SessionProfile), "profile is set by __init__"
        assert session.groups == [], "groups is set by __init__"
        assert session.environment == {}, "environment is set by __init__"
        assert session.default_object_perms == {}, "default_object_perms is set by __init__"

    def test__json_encode(self):
        app = SessionApp(id=uuid.uuid1(), app_id=uuid.uuid1(), app_name="test", config={})
        profile = SessionProfile(id=uuid.uuid1(), email="hi@example.com")
        session = Session(save=True, app=app, profile=profile, groups=[], environment={}, default_object_perms={})
        assert "save" not in json.loads(json.dumps(session, cls=JSONEncoder)), "save not exported"

    def test__overwrite(self):
        session = Session()
        with pytest.raises(ValueError):
            session.save

        session.overwrite(
            Session(save=True, app=SessionApp(), profile=SessionProfile(), groups=[], environment={},
                    default_object_perms={})
        )
        assert session.save == True, "save is set by overwrite"
        assert isinstance(session.app, SessionApp), "app is set by overwrite"
        assert isinstance(session.profile, SessionProfile), "profile is set by overwrite"
        assert session.groups == [], "groups is set by overwrite"
        assert session.environment == {}, "environment is set by overwrite"
        assert session.default_object_perms == {}, "default_object_perms is set by overwrite"

class TestSessionDecorator:
    def test__basic(self, request_context_with_session):
        # basic
        profile = mock.Mock()
        decorator = SessionDecorator(profile=profile)
        assert flask.session.profile is None, "profile is unset"
        with decorator:
            assert flask.session.profile is profile, "profile is set after entry"
        assert flask.session.profile is None, "profile is unset"

        # groups test
        decorator = SessionDecorator(groups=[groups.admin])
        assert flask.session.groups == [groups.everybody], "only everybody in groups list when not in context"
        with decorator:
            assert set(flask.session.groups) == set([groups.admin, groups.everybody]), \
                   "everybody in groups list in context"
        assert flask.session.groups == [groups.everybody], "groups list correctly reset on exit"

        decorator = SessionDecorator(extend_groups=False, groups=[groups.admin])
        assert flask.session.groups == [groups.everybody], "groups list correctly reset on exit"
        with decorator:
            assert flask.session.groups == [groups.admin], "groups list replaced in context if asked to"

        # different session
        real_session = Session(groups=[], profile=None, environment={}, app=None,
                               save=False, default_object_perms={})
        assert flask.session.groups == [groups.everybody], "groups list correctly reset on exit"

        decorator = SessionDecorator(extend_groups=True, groups=[groups.root], real_session=real_session)
        with decorator:
            assert flask.session.groups == [groups.everybody], "if flask is not the passed session, it's untouched"
            assert real_session.groups == [groups.root], "real session modified"

        assert real_session.groups == [], "real session reset after __exit__"
        assert flask.session.groups == [groups.everybody], "flask session still unmodified"

    def test__nested(self, request_context_with_session):
        # not sure if there is a legit practical reason for this
        decorator = SessionDecorator(groups=[groups.root])

        assert flask.session.groups == [groups.everybody], "groups list correctly set"
        with decorator:
            assert set(flask.session.groups) == set([groups.everybody, groups.root]), "groups list correct"

            with decorator:
                assert set(flask.session.groups) == set([groups.everybody, groups.root]), \
                       "groups list correct when nested"

            assert set(flask.session.groups) == set([groups.everybody, groups.root]), \
                   "groups list correct on first exit"

        assert flask.session.groups == [groups.everybody], "groups list correctly reset on exit"

    def test__as_decorator(self, request_context_with_session):
        ensure_call = mock.Mock()

        @SessionDecorator(groups=[groups.root])
        def test_decoration():
            assert set(flask.session.groups) == set([groups.everybody, groups.root]), "session modified in function"
            ensure_call()

        assert flask.session.groups == [groups.everybody], "just everybody before test"

        test_decoration()
        assert ensure_call.called, "function was actually called"

        assert flask.session.groups == [groups.everybody], "just everybody after test"


def test__do_with_groups(request_context_with_session):
    assert flask.session.groups == [groups.everybody], "test set"
    with do_with_groups(groups.root, groups.admin):
        assert set(flask.session.groups) == set([groups.everybody, groups.root, groups.admin]), "passed groups set by helper"
    assert flask.session.groups == [groups.everybody], "test reset"


def test__do_as_root(request_context_with_session):
    assert flask.session.groups == [groups.everybody], "test set right"
    with do_as_root:
        flask.session.groups == [groups.everybody, groups.root], "root installed"

    assert flask.session.groups == [groups.everybody], "test reset"
