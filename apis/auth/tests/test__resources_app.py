import pytest
from datetime import timezone

from directorofme.authorization import groups as groups_module
from directorofme_auth import app, db as real_db
from directorofme_auth import models
from directorofme.testing import dict_from_response, token_mock, existing, dump_and_load, comparable_links,\
                                 scoped_identity, group_of_one, json_request

unscoped_identity = scoped_identity(app)
authorized_for_read_identity = scoped_identity(app, real_db.Model.__scope__.read)
authorized_for_all_identity = scoped_identity(
    app, real_db.Model.__scope__.read, real_db.Model.__scope__.write, real_db.Model.__scope__.delete,
    groups_module.admin
)

public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDW3P3iU2MqiQa97H7+U+nryL2q
biW7HxBQ4CIhQGgV2U0FTM6sbJ/isGpls4poH26HD2CQSDLEkYvNr4pN61hr0tnm
TL8RijdaG/hM3XnFCcCdHF6b9i3SNNcoBTN63n0gmqkRE4Ev+yKVgrEYeRMw/keZ
Q6P9wwuIZFaJreDK4QIDAQAB
-----END PUBLIC KEY-----"""

@pytest.fixture
def app(db, request_context):
    scopes = models.Group.create_scope_groups(groups_module.Scope(display_name="test"))

    app = models.App(name="Test",
                     desc="Test",
                     url="https://example.com",
                     requested_access_groups=scopes)
    for obj in [app] + scopes:
        for (name, values) in authorized_for_all_identity["default_object_perms"].items():
            setattr(obj, name, values)
        obj.write = (groups_module.admin.name,)


    db.session.add(app)
    with real_db.Model.disable_permissions():
        db.session.commit()
        app = existing(app)
        app.requested_access_groups

    assert real_db.Model.permissions_enabled(), "permissions are on"
    yield app


class TestApp:
    def test__get(self, app, test_client):
        with token_mock(unscoped_identity):
            response = test_client.get("/api/-/auth/apps/{}".format(app.slug))
            assert response.status_code == 404, "unauthorized access returns a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("/api/-/auth/apps/{}".format(app.slug))
            assert response.status_code == 200, "successful select returns a 200"

        response = dict_from_response(response)
        response["requested_scopes"].sort()

        assert response == {
            "slug": app.slug,
            "name": app.name,
            "desc": app.desc,
            "url": app.url.url,
            "callback_url": None,
            "config_schema": None,
            "public_key": None,

            "requested_scopes": [ "test-delete", "test-read", "test-write" ],
            "created": app.created.replace(tzinfo=timezone.utc).isoformat(),
            "updated": app.updated.replace(tzinfo=timezone.utc).isoformat(),

            "_links": {
                "self": "/api/-/auth/apps/{}".format(app.slug),
                "collection": "/api/-/auth/apps/",
                "publish": "/api/-/auth/apps/{}/publish/f-user".format(app.slug)
            }
        }

    def test__put(self, db, app, test_client):
        url = "/api/-/auth/apps/{}".format(app.slug)
        put_obj = None
        with token_mock(authorized_for_read_identity) as mock_token:
            put_obj = dict_from_response(test_client.get(url))

        with token_mock(unscoped_identity):
            response = json_request(test_client, "put", url, data=put_obj)
            assert response.status_code == 404, "unauthorized access returns a 404"

        put_obj["desc"] = "Test Test Test"
        with token_mock(authorized_for_read_identity):
            response = json_request(test_client, "put", url, data=put_obj)
            assert response.status_code == 403, "read but no write returns a 403"

        db.session.rollback()
        put_obj["requested_scopes"] = [ "test-read" ]
        with token_mock(authorized_for_all_identity):
            response = json_request(test_client, "put", url, data=put_obj)
            assert response.status_code == 200, "success with no URL change"
            response = dict_from_response(response)
            assert response["desc"] == put_obj["desc"], "actually updated"
            assert response["requested_scopes"] == put_obj["requested_scopes"], "actually updated"

        put_obj["requested_scopes"] = [ "test-read", "test-nope" ]
        with token_mock(authorized_for_all_identity):
            response = json_request(test_client, "put", url, data=put_obj)
            assert response.status_code == 409, "non-existant scope throws 409"

        put_obj["requested_scopes"] = [ "test-read" ]
        del put_obj["name"]
        with token_mock(authorized_for_all_identity):
            response = json_request(test_client, "put", url, data=put_obj)
            assert response.status_code == 400, "missing required field 400s"

        put_obj["name"] = "A New Name"
        with token_mock(authorized_for_all_identity):
            response = json_request(test_client, "put", url, data=put_obj)
            assert response.status_code == 301, "successful name-change returns a 301"
            assert response.headers["Location"].endswith("/api/-/auth/apps/a-new-name"), "slug updated"


    def test__patch_as_differs_from_post(self, app, test_client):
        with token_mock(authorized_for_all_identity):
            response = json_request(test_client, "patch", "/api/-/auth/apps/{}".format(app.slug),
                                    data={ "desc": "TEST TEST TEST" })
            assert response.status_code == 200, "partial update succeeds"
            assert dict_from_response(response)["desc"] == "TEST TEST TEST", "actually updates"

    def test__jsonschema_validation(self, app, test_client):
        with token_mock(authorized_for_all_identity):
            response = json_request(test_client, "patch", "/api/-/auth/apps/{}".format(app.slug),
                                    data={ "config_schema": { "type": "foo"} })
            assert response.status_code == 400, "invalid schema fails with 400"

            response = json_request(test_client, "patch", "/api/-/auth/apps/{}".format(app.slug),
                                    data={ "config_schema": { "type": "object"} })
            assert response.status_code == 200, "valid schema saves just fine"
            assert dict_from_response(response)["config_schema"] == { "type": "object" }, "value saved"

    def test__rsa_publickey_validation(self, app, test_client):
        with token_mock(authorized_for_all_identity):
            response = json_request(test_client, "patch", "/api/-/auth/apps/{}".format(app.slug),
                                    data={ "public_key": "abcdefg" })
            assert response.status_code == 400, "invalid schema fails with 400"

            response = json_request(test_client, "patch", "/api/-/auth/apps/{}".format(app.slug),
                                    data={ "public_key": public_key})


class TestApps:
    pass
