import pytest
import uuid
import json

from directorofme.authorization.session import Session, SessionProfile, SessionApp
from directorofme.json import JSONEncoder

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
        assert Session.attributes == {"save", "app", "profile", "groups", "environment"}, "attributes correct"

        session = Session()
        assert isinstance(session, Session), "init works with no args"

        session = Session(save=True, app=SessionApp(), profile=SessionProfile(), groups=[], environment={})
        assert session.save == True, "save is set by __init__"
        assert isinstance(session.app, SessionApp), "app is set by __init__"
        assert isinstance(session.profile, SessionProfile), "profile is set by __init__"
        assert session.groups == [], "groups is set by __init__"
        assert session.environment == {}, "environment is set by __init__"

    def test__json_encode(self):
        app = SessionApp(id=uuid.uuid1(), app_id=uuid.uuid1(), app_name="test", config={})
        profile = SessionProfile(id=uuid.uuid1(), email="hi@example.com")
        session = Session(save=True, app=app, profile=profile, groups=[], environment={})
        assert "save" not in json.loads(json.dumps(session, cls=JSONEncoder)), "save not exported"

    def test__overwrite(self):
        session = Session()
        with pytest.raises(ValueError):
            session.save

        session.overwrite(
            Session(save=True, app=SessionApp(), profile=SessionProfile(), groups=[], environment={})
        )
        assert session.save == True, "save is set by overwrite"
        assert isinstance(session.app, SessionApp), "app is set by overwrite"
        assert isinstance(session.profile, SessionProfile), "profile is set by overwrite"
        assert session.groups == [], "groups is set by overwrite"
        assert session.environment == {}, "environment is set by overwrite"
