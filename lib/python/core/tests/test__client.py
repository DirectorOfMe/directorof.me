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

        response.status_code = 500
        response._content = b"text"
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
                mock_method.assert_called_with(url="https://test.directorof.me/api/-/foo/bar")

    def test__refresh(self, dom_client):
        with mock.patch.object(dom_client, "put") as mock_put:
            mock_put.return_value = { "session": True }
            assert dom_client.refresh() == { "session": True }, "refresh calls put"
            mock_put.assert_called_with("auth/refresh")
