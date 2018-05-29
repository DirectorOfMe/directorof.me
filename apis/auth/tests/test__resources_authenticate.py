import json
import uuid
import copy
import flask
import werkzeug
import pytest

from unittest import mock
from werkzeug.exceptions import NotFound, BadRequest, Unauthorized, Conflict
from oauthlib.oauth2 import OAuth2Error
from flask_jwt_extended.exceptions import NoAuthorizationError

from directorofme.testing import token_mock, dump_and_load, json_request, dict_from_response
from directorofme.authorization import groups, session
from directorofme.authorization.exceptions import PermissionDeniedError

from directorofme_auth import app, api, models, db as real_db
from directorofme.oauth import Client as OAuthClient, Google
from directorofme_auth.resources.authenticate import OAuth, OAuthCallback, Session, SessionForApp, \
                                                     with_service_client
### FIXTURES
test_auth_url = "https://example.com/auth?callback=mine"
@pytest.fixture
def authorization_url():
    with mock.patch("directorofme.oauth.Client.authorization_url") as method:
        method.return_value = test_auth_url
        yield method

empty_session_data = dump_and_load({
    "environment": {}, "groups": [groups.everybody], "app": None, "profile": None,
    "default_object_perms": { "read": (groups.everybody.name,) },
}, app)

test_session_data = dump_and_load({
    "app": None, "environment": {},
    "profile": { "id": uuid.uuid1(), "email": "hi@example.com" },
    "groups": [groups.everybody, groups.user, groups.Group(display_name="test", type=groups.GroupTypes.data)],
    "default_object_perms": { "read": (groups.everybody.name,) }
}, app)

def cookie_checker(response):
    cookies_should_be = [ "JWT_ACCESS_COOKIE_NAME", "JWT_REFRESH_COOKIE_NAME",
                          "JWT_ACCESS_CSRF_COOKIE_NAME", "JWT_REFRESH_CSRF_COOKIE_NAME" ]
    set_cookies = set([h.partition("=")[0] for h in response.headers.getlist("Set-Cookie")])
    assert set_cookies == { app.config[name] for name in cookies_should_be }, "cookies set correctly"


def session_should_be(data=None):
    response = dump_and_load(data or flask.session, app)
    response["default_object_perms"] = {k: list(v) for k,v in response["default_object_perms"].items()}
    response["_links"] = { "self": "/api/-/auth/session" }
    return response

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
    with mock.patch("directorofme.oauth.Google.fetch_token") as fetch_token:
        yield fetch_token

@pytest.fixture
def confirm_email(request_context):
    with mock.patch("directorofme.oauth.Google.confirm_email") as confirm_email:
        yield confirm_email


### TESTS
def test__with_service_client(request_context):
    @with_service_client
    def pass_through(*args):
        return args

    _, client = pass_through(None, "google")
    assert isinstance(client, OAuthClient), "client is an oauth client"
    assert isinstance(client, Google), "client is a google oauth client"

    with pytest.raises(NotFound):
        pass_through(None, "not_a_service")


class TestOAuth:
    def test__get_method_directly(self, request_context, authorization_url):
        response, response_code, headers = OAuth().get("google")
        assert response == { "auth_url": test_auth_url }, "url is correct"
        assert response_code == 302, "temporary redirect"
        assert headers == { "Location": test_auth_url }, "Location header is correctly set"

        installed_app_id = uuid.uuid1()
        flask.request.values.dicts.append(werkzeug.MultiDict([("installed_app_id", str(installed_app_id))]))
        with mock.patch.object(api, "url_for") as url_for_mock:
            response, response_code, headers = OAuth().get("google")
            url_for_mock.assert_called_with(OAuthCallback, api_version="-", service="google", _external=True)
            assert headers == { "Location": test_auth_url }, "Location header is correctly set"

    def test__oauth_route(self, test_client, authorization_url):
        response = test_client.get("/api/-/auth/oauth/google")
        assert response.status_code == 302, "temporary redirect"
        assert response.headers["Location"] == test_auth_url
        assert response.get_json() == { "auth_url": test_auth_url }, "response object correct"



class TestOAuthCallback:
    def test__get_error_from_auth_endpoint(self, request_context):
        with mock.patch("directorofme.oauth.Google.check_callback_request_for_errors") as checker:
            checker.return_value = "Error"
            with pytest.raises(BadRequest):
                OAuthCallback().get("google")

            assert checker.called, "checker was used"

    def test__get_directly_error_if_email_unverified(self, fetch_token, confirm_email):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", False)

        with pytest.raises(BadRequest):
            OAuthCallback().get("google")

        assert all([m.called for m in (fetch_token, confirm_email)]), "mocks were called"

    def test__get_directly_error_if_oauth_error(self, fetch_token, confirm_email):
        fetch_token.side_effect = OAuth2Error()

        with pytest.raises(BadRequest):
            OAuthCallback().get("google")

    def test__get_directly_no_user(self, fetch_token, confirm_email):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", True)

        with pytest.raises(Unauthorized):
            OAuthCallback().get("google")


    def test__get_directly_no_app(self, fetch_token, confirm_email, test_profile, request_context):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", True)

        assert OAuthCallback().get("google")[0] is not None, "profile exists"

        flask.request.values.dicts.append(werkzeug.MultiDict([("state", str(uuid.uuid1()))]))
        with pytest.raises(Conflict):
            OAuthCallback().get("google")

    def test__get_directly_happypaths(self, fetch_token, confirm_email, test_profile):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", True)

        session_obj, status_code, headers = OAuthCallback().get("google")
        assert session_obj == session_should_be(), "session set and returned by login"
        assert status_code == 201, "201 response code"
        assert headers == { "Location": "/api/-/auth/session" }, "location header set"
        assert flask.session.profile.email == test_profile.email, "profile set"
        assert flask.session.save, "session is updated by login"

        installed_app = None
        with session.do_with_groups(groups.Group.from_conforming_type(test_profile.group_of_one)):
            installed_app = models.InstalledApp.query.first()
            flask.request.values.dicts.append(werkzeug.MultiDict([("state", str(installed_app.id))]))

        assert OAuthCallback().get("google")[0] == session_should_be(), "session set and returned by login"
        assert flask.session.app.id == installed_app.id, "correct test app installed"
        assert set(
            groups.Group.from_conforming_type(g) for g in installed_app.access_groups
        ).issubset(set(flask.session.groups)), "app group in session"
        assert flask.session.save, "session is updated by login"

    def test__oauth_callback_route(self, fetch_token, confirm_email, test_profile, test_client, db):
        fetch_token.return_value = "token"
        confirm_email.return_value = ("test@example.com", True)

        db.session.expire_all()
        with real_db.Model.enable_permissions():
            response = test_client.get("/api/-/auth/oauth/google/callback")

            cookie_checker(response)
            assert response.status_code == 201, "response code is a 201"
            assert response.headers["Location"].endswith("/api/-/auth/session"), "location is correct"
            assert response.get_json() == session_should_be(), "response object correct for login"

    def test__end_to_end(self, fetch_token, confirm_email, test_client, test_profile, db):
        fetch_token.return_value = "token",
        confirm_email.return_value = (test_profile.email, True)

        db.session.expire_all()
        with real_db.Model.enable_permissions():
            response = test_client.get("/api/-/auth/oauth/google/callback")

        cookie_checker(response)
        response_dict = response.get_json()
        response_dict["groups"].sort(key=lambda x: x["name"])
        assert response_dict == session_should_be({
            "environment": {},
            "profile": { "id": str(test_profile.id), "email": test_profile.email },
            "groups": sorted([
                dump_and_load(groups.everybody, app),
                dump_and_load(groups.user, app),
                dump_and_load(groups.Group.from_conforming_type(test_profile.group_of_one), app),
                dump_and_load(real_db.Model.__scope__.read, app)
            ], key=lambda x: x["name"]),
            "app": None,
            "default_object_perms": {
                "read": [test_profile.group_of_one.name],
                "write": [test_profile.group_of_one.name],
                "delete": [test_profile.group_of_one.name]
            }
        }), "session is correctly formed"


class TestSession:
    def test__get_method_directly(self, request_context):
        with pytest.raises(PermissionDeniedError):
            Session().get()

        with session.do_with_groups(groups.user):
            assert dump_and_load(Session().get()) == session_should_be(), "session returns flask.session"

    def test__session_route(self, test_client):
        response = test_client.get("/api/-/auth/session")
        assert response.status_code == 403, "permission denied to non-user"

        with token_mock(copy.deepcopy(test_session_data)) as mocked_token:
            response = test_client.get("/api/-/auth/session")
            assert mocked_token.called, "mock was used correctly"
            assert response.get_json() == session_should_be(test_session_data), \
                   "correct session for logged-in user"

    def test__put_method_directly(self, refresh_token_decoder):
        assert dump_and_load(flask.session, app) == empty_session_data, "session is empty"

        session_obj = Session().put()
        assert session_obj == session_should_be(), "session is saved by the refresh method"
        assert dump_and_load(session_obj, app) == session_should_be(test_session_data), "session data correct"

        test_app =  { "id": uuid.uuid1(), "app_id": uuid.uuid1(), "app_slug": "foo", "config": {} }
        with mock.patch.dict(test_session_data, {"app": test_app}):
            session_obj = Session().put()
            assert uuid.UUID(session_obj["app"]["id"]) == test_app["id"], "session app is set"
            assert isinstance(flask.session.app, session.SessionApp), "session app is set in flask session"

        with mock.patch.dict(test_session_data, {"groups": [{}]}):
            with pytest.raises(BadRequest):
               Session().put()

    def test___put_route(self, refresh_token_decoder, test_client):
        response = test_client.put("/api/-/auth/session")
        assert response.get_json() == session_should_be(test_session_data), "response object correct"
        assert response.status_code == 200, "200 response code"


class TestSessionForApp:
    def test__get_method_directly(self, request_context, test_profile):
        session_profile = session.SessionProfile.from_conforming_type(test_profile)
        with session.do_with_groups(groups.user), \
                 mock.patch.object(flask.session, "profile", session_profile):
            assert flask.session.app is None, "no app"
            installed_app = models.InstalledApp.query.first()
            assert installed_app.app_slug == "main", "app is correct"

            session_obj, status_code, headers = SessionForApp().post(str(installed_app.id))
            assert session_obj == session_should_be(), "session is overwritten"
            assert status_code == 201, "status code is 201"
            assert headers == { "Location": "/api/-/auth/session" }, "header set"
            assert flask.session.save, "session is marked for save"
            assert uuid.UUID(session_obj["app"]["id"]) == installed_app.id, "app is correctly set"

    def test__sessionforapp_route(self, test_profile, test_client):
        session_no_app = None
        installed_app = None
        session_profile = session.SessionProfile.from_conforming_type(test_profile)
        with session.do_with_groups(groups.user):
            with mock.patch.object(flask.session, "profile", session_profile):
                session_no_app = dump_and_load(flask.session, app)
                installed_app = models.InstalledApp.query.first()
                assert installed_app.app_slug == "main", "app is correct"

        with token_mock(copy.deepcopy(session_no_app)) as mocked_token:
            response = test_client.post("/api/-/auth/session/{}".format(installed_app.id))
            assert mocked_token.called, "mock was used"
            assert response.get_json()["app"]["id"] == str(installed_app.id), "app installed"
            assert response.status_code == 201, "status code is 201"
            assert response.headers["Location"].endswith("/api/-/auth/session"), "location is correct"

            response = test_client.post("/api/-/auth/session/{}".format(str(uuid.uuid1())))
            assert response.status_code == 404, "Not found UUID returns 404"


admin_session = dump_and_load({
    "app": None, "environment": {},
    "profile": { "id": uuid.uuid1(), "email": "hi@example.com" },
    "groups": [groups.everybody, groups.admin, groups.user],
    "default_object_perms": { "read": (groups.everybody.name,) }
}, app)

class TestSudo:
    def test__post_no_admin(self, test_client):
        with token_mock(test_session_data) as mocked_token:
            response = json_request(test_client, "post", "/api/-/auth/sudo/hi@example.com", data={})
            assert response.status_code == 403, "permission denied to non-admin"

    def test__post_no_profile(self, test_client):
        with token_mock(admin_session) as mocked_token:
            response = json_request(test_client, "post", "/api/-/auth/sudo/test@example.com", data={})
            assert response.status_code == 404, "Unauthorized if no profile exists"

    def test__post_happypath(self, request_context, test_client, test_profile):
        with token_mock(admin_session) as mocked_token:
            response = json_request(test_client, "post", "/api/-/auth/sudo/test@example.com", data={})
            assert response.status_code == 201, "Success"
            assert response.headers["Location"].endswith("/api/-/auth/session"), "location header set"
            assert dict_from_response(response)["profile"]["email"] == "test@example.com", "profile switched"
            assert dict_from_response(response)["app"] is None, "no app if app isn't passed"
            cookie_checker(response)

    def test__post_with_app(self, request_context, test_profile, test_client):
        installed_app_id = str(models.InstalledApp.query.first().id)
        with token_mock(admin_session) as mocked_token:
            url = "/api/-/auth/sudo/test@example.com?installed_app_id={}".format(installed_app_id)
            response = json_request(test_client, "post", url, data={})
            assert response.status_code == 201, "Success"
            assert dict_from_response(response)["app"]["id"] == installed_app_id, "app installed"

            url = "/api/-/auth/sudo/test@example.com?installed_app_id=abc"
            response = json_request(test_client, "post", url, data={})
            assert response.status_code == 400, "Bad UUID returns 400"

            url = "/api/-/auth/sudo/test@example.com?installed_app_id={}".format(str(uuid.uuid1()))
            response = json_request(test_client, "post", url, data={})
            assert response.status_code == 409, "Not found UUID returns 409"
