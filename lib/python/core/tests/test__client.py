import pytest
import json
import requests

from unittest import mock
from directorofme import client

DOM = client.DOM

@pytest.fixture
def dom_client():
    yield DOM("test.directorof.me")

class TestDOM:
    def test__init__(self):
        assert "X-CSRF-TOKEN" not in DOM("test.directorof.me").headers, "no headers set if no CSRF passed"
        assert "X-CSRF-REFRESH-TOKEN" not in DOM("test.directorof.me").headers, "no headers set if no CSRF passed"

        assert DOM("test.directorof.me").cookies == {}, "no headers set if no tokens passed"

        assert DOM("test.directorof.me", access_csrf_token="csrf").headers["X-CSRF-TOKEN"] == "csrf", \
               "headers set when csrf passed"
        assert DOM("test.directorof.me", refresh_csrf_token="csrf").headers["X-CSRF-REFRESH-TOKEN"] == "csrf", \
               "headers set when csrf passed"

        cookies = DOM("test.directorof.me", access_token="access", refresh_token="refresh").cookies
        assert cookies["access_token_cookie"] == "access", "cookies set from pased tokens"
        assert cookies["refresh_token_cookie"] == "refresh", "cookies set from pased tokens"

    def test__url(self):
        assert DOM("test.directorof.me").url("api_name/api_endpoint") == \
               "https://test.directorof.me/api/-/api_name/api_endpoint", "url works with default version"
        assert DOM("test.directorof.me", version="3").url("api_name/api_endpoint") == \
               "https://test.directorof.me/api/3/api_name/api_endpoint", "url works with passed version"

    def test__check(self, dom_client):
        response = requests.Response()
        response._content = bytes(json.dumps({ "message": "message" }), "utf8")

        for status_code in (204, 304):
            response.status_code = status_code
            assert dom_client.check(response) is None, "*04s return None"

        for status_code in (200, 201, 301, 302):
            response.status_code = status_code
            assert dom_client.check(response) == { "message": "message" }, "success status codes return objects"

        response.status_code = 400
        with pytest.raises(client.BadRequest, match=r".*message.*"):
            dom_client.check(response)

        response.status_code = 401
        with pytest.raises(client.Unauthorized, match=r".*message.*"):
            dom_client.check(response)

        response.status_code = 403
        with pytest.raises(client.PermissionDenied, match=r".*message.*"):
            dom_client.check(response)

        response.status_code = 404
        with pytest.raises(client.NotFound, match=r".*message.*"):
            dom_client.check(response)

        response.status_code = 409
        response._content = b"text"
        with pytest.raises(client.Conflict, match=r".*text.*"):
            dom_client.check(response)

        response.status_code = 500
        with pytest.raises(client.ServerError, match=r".*text.*"):
            dom_client.check(response)

    def test__verbs(self, dom_client):
        for method in ("get", "post", "put", "patch", "delete"):
            response = requests.Response()
            response.status_code = 200
            response._content = bytes(json.dumps({ "test":  method }), "utf8")

            with mock.patch("requests.Session.{}".format(method)) as mock_method:
                mock_method.return_value = response
                assert getattr(dom_client, method)("foo/bar") == { "test": method }, "method pass-through works"
                kwargs = { "url": "https://test.directorof.me/api/-/foo/bar" }
                if method != "get":
                    kwargs["json"] = None
                mock_method.assert_called_with(**kwargs)

    def test__refresh(self, dom_client):
        def mock_put_side_effect(*args, **kwargs):
            dom_client.cookies["csrf_access_token"] = "csrf_access_token"
            dom_client.cookies["csrf_refresh_token"] = "csrf_refresh_token"
            return { "session": True }

        with mock.patch.object(dom_client, "put") as mock_put:
            mock_put.side_effect = mock_put_side_effect
            assert dom_client.refresh() == { "session": True }, "refresh calls put"
            mock_put.assert_called_with("auth/session")
            assert dom_client.headers["X-CSRF-TOKEN"] == "csrf_access_token"
            assert dom_client.headers["X-CSRF-REFRESH-TOKEN"] == "csrf_refresh_token"

    def test__from_request(self, app):
        class MockRequest:
            def __init__(self, host, access_token, csrf_token, refresh_token, refresh_csrf_token):
                self.host = host
                self.cookies = {
                    "access_token_cookie": access_token,
                    "refresh_token_cookie": refresh_token
                }
                self.headers = {
                    "X-CSRF-TOKEN": csrf_token,
                    "X-CSRF-REFRESH-TOKEN": refresh_csrf_token
                }

        client = DOM.from_request(MockRequest("test.example.com", "access", "csrf", "refresh", "refresh_csrf"))
        assert client.url("foo") == "https://test.example.com/api/-/foo", "host set from request"
        assert client.cookies["access_token_cookie"] == "access", "access cookie set from request cookie"
        assert client.cookies["refresh_token_cookie"] == "refresh", "refresh cookie set from request cookie"

        assert client.headers["X-CSRF-TOKEN"] == "csrf", "csrf header set from request"
        assert client.headers["X-CSRF-REFRESH-TOKEN"] == "refresh_csrf", "request csrf header set from request"

        with mock.patch("flask_jwt_extended.get_csrf_token") as get_csrf_token:
            get_csrf_token.return_value = "got_csrf"
            client = DOM.from_request(MockRequest("test.example.com", "access", "csrf", "refresh", None), app)

            assert get_csrf_token.called, "csrf mock called"
            assert client.headers["X-CSRF-TOKEN"] == "csrf", "csrf installed from request"
            assert client.headers["X-CSRF-REFRESH-TOKEN"] == "got_csrf", "csrf installed from token"

            get_csrf_token.reset_mock()
            client = DOM.from_request(
                MockRequest("test.example.com", "access", None, "refresh", "refresh_csrf"),
                app
            )

            assert get_csrf_token.called, "csrf mock called"
            assert client.headers["X-CSRF-TOKEN"] == "got_csrf", "csrf installed from token"
            assert client.headers["X-CSRF-REFRESH-TOKEN"] == "refresh_csrf", "csrf installed from header"

    def test__from_installed_app(self):
        class Cipher:
            def decrypt(self, value):
                return value

        installed_app = {
            "config": {
                "integrations": {
                    "directorofme": {
                        "refresh_token": {
                            "encryption": "RSA",
                            "value": "encrypted refresh_token"
                        },
                        "refresh_csrf_token": {
                            "encryption": "RSA",
                            "value": "encrypted refresh_csrf_token"
                        },
                    }
                }
            }
        }

        with mock.patch.object(DOM, "refresh") as mock_refresh:
            client = DOM.from_installed_app("test.example.com", Cipher(), installed_app)

            assert mock_refresh.called, "client refreshed"
            assert client.cookies["refresh_token_cookie"] == "encrypted refresh_token", "refresh cookie works"
            assert client.headers["X-CSRF-REFRESH-TOKEN"] == "encrypted refresh_csrf_token", "refresh csrf works"

        with pytest.raises(ValueError):
            DOM.from_installed_app("test.example.com", Cipher(), {})

        del installed_app["config"]["integrations"]["directorofme"]["refresh_token"]["value"]
        with pytest.raises(ValueError):
            DOM.from_installed_app("test.example.com", Cipher(), installed_app)
