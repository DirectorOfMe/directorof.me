import pytest
import copy

from unittest import mock

from requests_oauthlib import OAuth2Session
from directorofme.authorization.exceptions import MisconfiguredAuthError
from directorofme_auth import config
from directorofme_auth.oauth import Client, Google

@pytest.fixture
def clean_clientmeta():
    original_registry = copy.deepcopy(type(Client).registry)
    yield
    type(Client).registry = original_registry
@pytest.fixture
def oauth_client():
    return Client(callback_url="https://example.com/us/callback",
                  client_id="client-id-123",
                  client_secret="client-secret",
                  auth_url="https://example.com/them/auth",
                  token_url="https://example.com/them/token",
                  auth_kwargs={},
                  session_kwargs={})

@pytest.fixture
def google_config():
    original_config = copy.deepcopy(config)
    config["GOOGLE_CLIENT_ID"] = "google-id"
    config["GOOGLE_CLIENT_SECRET"] = "google-secret"
    config["GOOGLE_AUTH_URL"] = "https://google.com/auth"
    config["GOOGLE_TOKEN_URL"] = "https://google.com/token"
    yield
    config.update(original_config)

google_scopes = { "scope": [ "https://www.googleapis.com/auth/userinfo.email",
                             "https://www.googleapis.com/auth/userinfo.profile" ] }


class TestClient:
    def test__client_by_name(clean_clientmeta):
        assert Client.client_by_name("sub") is None, "no sub if not created yet"

        class SubClient(Client):
            name = "sub" 
        assert Client.client_by_name("sub") is SubClient, "SubClient registered properly"

        with pytest.raises(TypeError):
            # re-registering with the same name breaks
            class Sub2Client(Client):
                name = "sub"

    def test__init__(self, oauth_client):
        assert oauth_client.client_id == "client-id-123", "client_id is set"
        assert oauth_client.client_secret == "client-secret", "client_secret is set"
        assert oauth_client.auth_url == "https://example.com/them/auth", "auth_url is set"
        assert oauth_client.token_url == "https://example.com/them/token", "token_url is set"
        assert oauth_client.auth_kwargs == {}, "auth_kwargs are set"
        assert isinstance(oauth_client.session, OAuth2Session), "session set"

    def test__getattr__(self, oauth_client):
        with mock.patch("requests_oauthlib.OAuth2Session.get") as get:
            oauth_client.get("/foo")
            assert get.called_with("/foo")

        with pytest.raises(AttributeError):
            oauth_client.does_not_exist

    def test__confirm_email_is_abstract(self, oauth_client):
        with pytest.raises(NotImplementedError):
            oauth_client.confirm_email()

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
    @mock.patch("requests_oauthlib.oauth2_session.OAuth2Session.__new__")
    def test__init__(self, SessionMock, google_config):
        client = Google("/callback")
        assert client.client_id == "google-id", "google id set from config"
        assert client.client_secret == "google-secret", "google secret set from config"
        assert client.auth_url == "https://google.com/auth", "google auth_url set from config"
        assert client.token_url == "https://google.com/token", "google token_url set from config"
        assert tuple(client.auth_kwargs.keys()) == ("prompt",), "auth_kwargs set from config"
        SessionMock.assert_called_with(OAuth2Session, "google-id", redirect_uri="/callback", **google_scopes)

    @mock.patch("requests_oauthlib.oauth2_session.OAuth2Session.__new__")
    def test__confirm_email(self, SessionMock, google_config):
        client = Google("/callback")

        ResponseMock = mock.MagicMock()
        ResponseMock.json.return_value =  { "email": "me@example.com", "email_verified": True }
        client.session.get= mock.MagicMock()
        client.session.get.return_value = ResponseMock

        assert client.confirm_email(token={ "id_token": "token" }) == ("me@example.com", True), \
               "return value is correct"
        client.session.get.assert_called_with("https://www.googleapis.com/oauth2/v3/tokeninfo",
                                              params={ "id_token": "token" })
        assert ResponseMock.json.called, "json mock was correctly installed"
