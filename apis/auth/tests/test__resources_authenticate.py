import json
import copy
import flask
import pytest

from unittest import mock
from werkzeug.exceptions import NotFound, BadRequest
from oauthlib.oauth2 import OAuth2Error
from flask_jwt_extended.exceptions import NoAuthorizationError

from directorofme.testing import dict_from_response

from directorofme_auth import app
from directorofme_auth.oauth import Client as OAuthClient, Google
from directorofme_auth.resources.authenticate import OAuth, OAuthCallback, RefreshToken, Session,\
                                                     with_service_client
### FIXTURES
test_auth_url = "https://example.com/auth?callback=mine"
@pytest.fixture
def authorization_url():
    with mock.patch("directorofme_auth.oauth.Client.authorization_url") as method:
        method.return_value = test_auth_url
        yield method

empty_session_data = { "environment": {}, "groups": [], "app": None, "profile": None }
test_session_data = {
    "app": None, "environment": {},
    "profile": { "id": "12345", "email": "hi@example.com" },
    "groups": [{ "type": "data", "display_name": "test", "name": "d-test" }],
}

@pytest.fixture
def refresh_token_decoder(request_context):
    with mock.patch("flask_jwt_extended.view_decorators._decode_jwt_from_cookies") as decoder:
        def token_chooser(request_type="access"):
            if request_type == "access":
                raise NoAuthorizationError()
            return {
                "identity": copy.deepcopy(test_session_data),
                "type": "refresh",
                "user_claims": None
            }

        decoder.side_effect = token_chooser
        yield decoder


@pytest.fixture
def fetch_token(request_context):
    with mock.patch("directorofme_auth.oauth.Google.fetch_token") as fetch_token:
        yield fetch_token

@pytest.fixture
def confirm_email(request_context):
    with mock.patch("directorofme_auth.oauth.Google.confirm_email") as confirm_email:
        yield confirm_email


### TESTS
def test__with_service_client(request_context):
    @with_service_client
    def pass_through(*args):
        return args

    _, client, method = pass_through(None, "google", "login")
    assert isinstance(client, OAuthClient), "client is an oauth client"
    assert isinstance(client, Google), "client is a google oauth client"
    assert method == "login", "method is login"

    _, client, method = pass_through(None, "google", "token")
    assert method == "token", "method is token"

    with pytest.raises(NotFound):
        pass_through(None, "not_a_service", "login")

    with pytest.raises(NotFound):
        pass_through(None, "google", "not_a_method")


class TestOAuth:
    def test__get_method_directly(self, request_context, authorization_url):
        response, response_code, headers = OAuth().get("google", "login")
        assert response == { "auth_url": test_auth_url }, "url is correct"
        assert response_code == 302, "temporary redirect"
        assert headers == { "Location": test_auth_url }, "Location header is correctly set"

    def test__oauth_route(self, test_client, authorization_url):
        response = test_client.get("/api/-/auth/oauth/google/login")
        assert response.status_code == 302, "temporary redirect"
        assert response.headers["Location"] == test_auth_url
        assert dict_from_response(response) == { "auth_url": test_auth_url }, "response object correct"



class TestOAuthCallback:
    def test__get_error_from_auth_endpoint(self, request_context):
        with mock.patch("directorofme_auth.oauth.Google.check_callback_request_for_errors") as checker:
            checker.return_value = "Error"
            with pytest.raises(BadRequest):
                OAuthCallback().get("google", "token")

            assert checker.called, "checker was used"

    def test__get_directly_error_if_email_unverified(self, fetch_token, confirm_email):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", False)

        with pytest.raises(BadRequest):
            OAuthCallback().get("google", "token")

        assert all([m.called for m in (fetch_token, confirm_email)]), "mocks were called"

    def test__get_directly_error_if_oauth_error(self, fetch_token, confirm_email):
        fetch_token.side_effect = OAuth2Error()

        with pytest.raises(BadRequest):
            OAuthCallback().get("google", "token")

    def test__get_directly_no_user(self, fetch_token, confirm_email):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", True)

        with pytest.raises(NotFound):
            OAuthCallback().get("google", "token")

    def test__get_directly_happypaths(self, fetch_token, confirm_email, test_profile):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", True)

        assert OAuthCallback().get("google", "token") == { "service": "google", "token": "token" }, \
               "token returned successfully when user exists"

        assert not flask.session.save, "session not updated by token request"

        OAuthCallback().get("google", "login") is flask.session, "session set and returned by login"
        assert flask.session.profile.email == test_profile.email, "profile set"
        assert flask.session.save, "session is updated by login"

    def test__login_groups_handling(self):
        """TODO: when app groups are mixed in, we'll need to test this"""
        pass

    def test__oauth_callback_route(self, fetch_token, confirm_email, test_profile, test_client):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", True)

        response = test_client.get("/api/-/auth/oauth/google/token/callback")
        assert len(response.headers.getlist("Set-Cookie")) == 0, "no cookies set"
        assert dict_from_response(response) == { "service": "google", "token": "token" }, \
               "response object correct for token"

        response = test_client.get("/api/-/auth/oauth/google/login/callback")
        cookies_should_be = [ "JWT_ACCESS_COOKIE_NAME", "JWT_REFRESH_COOKIE_NAME",
                              "JWT_ACCESS_CSRF_COOKIE_NAME", "JWT_REFRESH_CSRF_COOKIE_NAME" ]
        set_cookies = set([h.partition("=")[0] for h in response.headers.getlist("Set-Cookie")])
        assert set_cookies == { app.config[name] for name in cookies_should_be }, "cookies set correctly"
        assert dict_from_response(response) == json.loads(json.dumps(flask.session, cls=app.json_encoder)), \
               "response object correct for login"


class TestRefreshToken:
    def test__get_method_directly(self, refresh_token_decoder):
        assert json.loads(json.dumps(flask.session, cls=app.json_encoder)) == empty_session_data, \
               "session is empty before test"

        session = RefreshToken().get()
        assert session == flask.session, "session is saved by the refresh method"
        assert json.loads(json.dumps(session, cls=app.json_encoder)) == test_session_data, \
               "session data returned correctly"

    def test__refresh_route(self, refresh_token_decoder, test_client):
        response = test_client.get("/api/-/auth/refresh")
        assert dict_from_response(response) == test_session_data, "response object correct"


class TestSession:
    def test__get_method_directly(self, request_context):
        with mock.patch("flask.session") as session:
            assert Session().get() is session, "session returns flask.session"

    def test__session_route(self, test_client):
        response = test_client.get("/api/-/auth/session")
        assert dict_from_response(response) == empty_session_data, "default session returned by default"
