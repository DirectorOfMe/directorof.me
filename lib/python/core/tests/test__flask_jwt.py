import flask
import pytest
from unittest import mock

from jwt.exceptions import InvalidTokenError
from flask_jwt_extended.exceptions import NoAuthorizationError

from directorofme.testing import token_mock
from directorofme.authorization import groups
from directorofme.authorization.exceptions import MisconfiguredAuthError
from directorofme.flask import JWTSessionInterface, JWTManager

class TestJWTSessionInterface:
    mock_identity = {
        "profile": { "id": 1, "email": "hi@example.com" },
        "groups": [], "environment": {},
        "app": { "id": 1, "app_id": 2, "app_name": "main", "config": {} },
        "default_object_perms": { "read": (groups.user.name,) },
    }

    def test__open_session(self, app):
        app.config["JWT_PUBLIC_KEY"] = "public key (fake)"
        JWTManager(app)

        # happy path
        with token_mock(self.mock_identity) as decode_mock:
            with app.test_request_context():
                session = flask.session
                assert decode_mock.called, "mock was installed correctly"
                assert session.profile.email == "hi@example.com", "session profile installed"
                assert session.app.app_name == "main", "session app installed"
                assert session.default_object_perms == self.mock_identity["default_object_perms"], \
                       "default object perms installed"

        # invalid token errors are ignored
        with token_mock() as decode_mock:
            decode_mock.side_effect = InvalidTokenError("Invalid Token")
            with app.test_request_context():
                session = flask.session
                assert decode_mock.called, "mock was installed correctly"
                assert session.profile is None, "invalid token installs empty session"
                assert session.groups == [groups.everybody], "groups list is [everybody]"
                assert session.default_object_perms == { "read": (groups.everybody.name,) }, \
                       "default object perms default correctly"

        # no header = empty session
        with token_mock() as decode_mock:
            decode_mock.side_effect = NoAuthorizationError("No Token")
            with app.test_request_context():
                session = flask.session
                assert decode_mock.called, "mock was installed correctly"
                assert session.profile is None, "no token installs empty session"
                assert session.groups == [groups.everybody], "groups list is [everybody]"
                assert session.default_object_perms == { "read": (groups.everybody.name,) }, \
                       "default object perms default correctly"

    def test__save_session(self, app):
        app.config["IS_AUTH_SERVER"] = True
        app.config["JWT_PUBLIC_KEY"] = "public key (fake)"
        app.config["JWT_PRIVATE_KEY"] = "private key (fake)"

        JWTManager(app)

        with mock.patch("flask_jwt_extended.create_access_token") as access_mock, \
                 mock.patch("flask_jwt_extended.create_refresh_token") as refresh_mock, \
                 mock.patch("flask_jwt_extended.utils.get_csrf_token") as csrf_mock:
            access_mock.return_value = "access"
            refresh_mock.return_value = "refresh"
            csrf_mock.return_value = "csrf"

            with app.test_request_context():
                #session.save is false, no save happens
                response = flask.Response()
                app.session_interface.save_session(app, flask.session, response)
                assert not access_mock.called, "access mock not called if save not set"
                assert not refresh_mock.called, "refresh mock not called if save not set"
                assert not csrf_mock.called, "refresh mock not called if save not set"

                flask.session.save = True
                app.config["IS_AUTH_SERVER"] = False
                app.session_interface.save_session(app, flask.session, response)
                assert not access_mock.called, "access mock not called if not auth server"
                assert not refresh_mock.called, "refresh mock not called if not auth server"
                assert not csrf_mock.called, "refresh mock not called if not auth server"

                app.config["IS_AUTH_SERVER"] = True
                app.session_interface.save_session(app, flask.session, response)
                assert access_mock.called, "access_mock called"
                assert refresh_mock.called, "refresh_mock called"
                assert csrf_mock.called, "csrf_mock called"

                seen = set()
                for name, value in response.headers.items():
                    if name == "Set-Cookie":
                        if value.startswith("access_token_cookie=access; HttpOnly;"):
                            seen.add("access_token_cookie")
                        elif value.startswith("refresh_token_cookie=refresh; HttpOnly;"):
                            seen.add("refresh_token_cookie")
                        elif value.startswith("csrf_access_token=csrf"):
                            seen.add("csrf_access_token")
                        elif value.startswith("csrf_refresh_token=csrf"):
                            seen.add("csrf_refresh_token")

                assert seen == {
                    "access_token_cookie", "refresh_token_cookie", "csrf_access_token", "csrf_refresh_token"
                }, "all cookies are correctly set"


class TestJWTManager:
    def test__init_app_calls_configure_app(self, app):
        with mock.patch('directorofme.flask.jwt.JWTManager.configure_app') as ConfigureAppMock:
            jwt = JWTManager()
            ConfigureAppMock.assert_not_called()

            jwt.init_app(app)
            ConfigureAppMock.assert_called_with(app)

        with mock.patch('directorofme.flask.jwt.JWTManager.configure_app') as ConfigureAppMock:
            jwt = JWTManager(app)
            ConfigureAppMock.assert_called_with(app)


    def test__configure_app_auth_server(self, app):
        app.config["IS_AUTH_SERVER"] = True
        app.config["JWT_PUBLIC_KEY"] = "public key (fake)"
        app.config["JWT_PRIVATE_KEY"] = "private key (fake)"

        JWTManager(app)
        assert app.config["JWT_TOKEN_LOCATION"] == ["cookies"], "tokens stored in cookies"
        assert app.config["JWT_COOKIE_CSRF_PROTECT"], "CSRF protection is enabled"
        assert app.config["JWT_ALGORITHM"] == "ES512", "ES512 algorithm selected"
        assert isinstance(app.session_interface, JWTSessionInterface)

    def test__configure_app_non_auth_server(self, app):
        app.config["IS_AUTH_SERVER"] = False
        app.config["JWT_PUBLIC_KEY"] = "public key (fake)"

        JWTManager(app)
        assert app.config["JWT_TOKEN_LOCATION"] == ["cookies"], "tokens stored in cookies"
        assert app.config["JWT_COOKIE_CSRF_PROTECT"], "CSRF protection is enabled"
        assert app.config["JWT_ALGORITHM"] == "ES512", "ES512 algorithm selected"
        assert isinstance(app.session_interface, JWTSessionInterface)

    def test__configure_app_fails_when_misconfigured(self, app):
        with pytest.raises(MisconfiguredAuthError):
            # no public key set
            JWTManager(app)

        app.config["JWT_PUBLIC_KEY"] = "public key (fake)"
        assert isinstance(JWTManager(app), JWTManager), "non auth server doesn't throw"

        app.config["JWT_PRIVATE_KEY"] = "private key (fake)"
        with pytest.raises(MisconfiguredAuthError):
            # private key set for non-auth-server
            JWTManager(app)

        del app.config["JWT_PRIVATE_KEY"]
        app.config["IS_AUTH_SERVER"] = True
        with pytest.raises(MisconfiguredAuthError):
            # auth server with no private key fails
            JWTManager(app)
