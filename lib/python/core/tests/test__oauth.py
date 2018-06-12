import pytest
import flask
import werkzeug
import copy
import contextlib

from unittest import mock
from oauthlib.oauth2 import OAuth2Error

from requests_oauthlib import OAuth2Session
from directorofme.authorization.exceptions import MisconfiguredAuthError
from directorofme.oauth import Client, Google, Slack

def _oauth_client(extra_kwargs=None):
    return Client(callback_url="https://example.com/us/callback",
                  client_id="client-id-123",
                  client_secret="client-secret",
                  auth_url="https://example.com/them/auth",
                  token_url="https://example.com/them/token",
                  auth_kwargs={},
                  session_kwargs={},
                  **(extra_kwargs or {}))

@pytest.fixture
def oauth_client():
    return _oauth_client()

@pytest.fixture
def google_config():
	yield {
		"GOOGLE_CLIENT_ID": "google-id",
    	"GOOGLE_CLIENT_SECRET": "google-secret",
    	"GOOGLE_AUTH_URL": "https://google.com/auth",
    	"GOOGLE_TOKEN_URL": "https://google.com/token"
	}

@pytest.fixture
def slack_config():
	yield {
		"SLACK_CLIENT_ID": "slack-id",
    	"SLACK_CLIENT_SECRET": "slack-secret",
    	"SLACK_AUTH_URL": "https://slack.com/auth",
    	"SLACK_TOKEN_URL": "https://slack.com/token",
        "SLACK_APP_ID": "A1234567"
	}


@contextlib.contextmanager
def mock_get(client, json_value):
    ResponseMock = mock.MagicMock()
    ResponseMock.json.return_value = json_value

    client.session = mock.MagicMock()
    with mock.patch.object(client.session, "get") as get_mock:
        get_mock.return_value = ResponseMock
        yield get_mock

google_scopes = { "scope": [ "https://www.googleapis.com/auth/userinfo.email",
                             "https://www.googleapis.com/auth/userinfo.profile" ] }


class TestClient:
    def test__init__(self, oauth_client):
        assert oauth_client.client_id == "client-id-123", "client_id is set"
        assert oauth_client.client_secret == "client-secret", "client_secret is set"
        assert oauth_client.auth_url == "https://example.com/them/auth", "auth_url is set"
        assert oauth_client.token_url == "https://example.com/them/token", "token_url is set"
        assert oauth_client.auth_kwargs == {}, "auth_kwargs are set"
        assert not oauth_client.offline, "offline defaults to False"
        assert isinstance(oauth_client.session, OAuth2Session), "session set"

        assert _oauth_client({ "offline": True }).offline, "if offline passed, offline is set"

    def test__getattr__(self, oauth_client):
        with mock.patch("requests_oauthlib.OAuth2Session.get") as get:
            oauth_client.get("/foo")
            assert get.called_with("/foo")

        with pytest.raises(AttributeError):
            oauth_client.does_not_exist

    def test__confirm_identity_is_abstract(self, oauth_client):
        with pytest.raises(NotImplementedError):
            oauth_client.confirm_identity()

    def test__check_callback_request_for_errors(self, request_context_with_session, oauth_client):
        assert oauth_client.check_callback_request_for_errors(flask.request) is None, "no errors returns None"

        flask.request.args = werkzeug.ImmutableMultiDict((("error", "Bad Error"),))
        assert oauth_client.check_callback_request_for_errors(flask.request) == "Bad Error", \
               "error msg returned when there is an error"

    def test__authorization_url(self, oauth_client):
        with mock.patch("requests_oauthlib.OAuth2Session.authorization_url") as authorization_url:
            oauth_client.authorization_url()
            authorization_url.assert_called_with(oauth_client.auth_url, **oauth_client.auth_kwargs)

    @mock.patch("requests_oauthlib.OAuth2Session.fetch_token")
    def test__fetch_token(self, fetch_token, oauth_client):
        oauth_client.fetch_token("/response")
        fetch_token.assert_called_with(oauth_client.token_url,
                                       client_secret=oauth_client.client_secret,
                                       authorization_response="/response")

        oauth_client.client_secret = None
        with pytest.raises(MisconfiguredAuthError):
            oauth_client.fetch_token("/response")


class TestGoogle:
    @mock.patch("requests_oauthlib.oauth2_session.OAuth2Session.__init__")
    def test__init__(self, SessionMock, google_config):
        SessionMock.return_value = None

        client = Google(google_config, callback_url="/callback")
        assert client.client_id == "google-id", "google id set from config"
        assert client.client_secret == "google-secret", "google secret set from config"
        assert client.auth_url == "https://google.com/auth", "google auth_url set from config"
        assert client.token_url == "https://google.com/token", "google token_url set from config"
        assert not client.offline, "offline defaults to False"
        assert tuple(client.auth_kwargs.keys()) == ("prompt",), "auth_kwargs set from config"
        SessionMock.assert_called_with("google-id", redirect_uri="/callback", state=None, **google_scopes)

        client = Google(google_config, callback_url="/callback", offline=True)
        assert client.offline, "offline set by __init__"
        assert sorted(client.auth_kwargs.keys()) == ["access_type", "prompt"], "access_type sent with auth_kwargs"

    def test__confirm_identity(self, google_config):
        client = Google(google_config, callback_url="/callback")

        with mock_get(client, { "name": "Me", "email": "me@example.com", "email_verified": True }) as get_mock:
            assert client.confirm_identity(token={ "id_token": "token" }) == ("me@example.com", True, "Me"), \
                   "return value is correct"
            get_mock.assert_called_with("https://www.googleapis.com/oauth2/v3/userinfo")


class TestSlack:
    @mock.patch("requests_oauthlib.oauth2_session.OAuth2Session.__init__")
    def test__init__(self, SessionMock, slack_config):
        SessionMock.return_value = None

        client = Slack(slack_config, callback_url="/callback")
        assert client.client_id == "slack-id", "slack id set from config"
        assert client.client_secret == "slack-secret", "slack secret set from config"
        assert client.auth_url == "https://slack.com/auth", "slack auth_url set from config"
        assert client.token_url == "https://slack.com/token", "slack token_url set from config"
        assert not client.offline, "offline defaults to False"
        assert client.auth_kwargs ==  {}, "auth_kwargs set from config"
        SessionMock.assert_called_with("slack-id", redirect_uri="/callback",
                                       scope="identity.basic,identity.email", state=None)

    def test__confirm_identity(self, slack_config):
        client = Slack(slack_config, callback_url="/callback")

        with mock_get(client, { "ok": True, "user": { "email": "me@example.com", "name": "Me" }}) as get_mock:
            assert client.confirm_identity() == ("me@example.com", True, "Me"), "return value is correct"
            get_mock.assert_called_with("https://slack.com/api/users.identity")

        with mock_get(client, { "ok": False }), pytest.raises(OAuth2Error):
            assert client.confirm_identity() == (None, False, None), "not ok returns no email"

    def test__app_url(self, slack_config):
        assert Slack(slack_config).app_url() == "https://slack.com/app_redirect?app=A1234567", "app_url works"
