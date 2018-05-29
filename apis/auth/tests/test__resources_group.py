import pytest
from datetime import timezone

from directorofme.authorization import groups as groups_module
from directorofme_auth import app, db as real_db
from directorofme_auth import models
from directorofme.testing import dict_from_response, token_mock, existing, dump_and_load, comparable_links,\
                                 scoped_identity, group_of_one, json_request

### TESTING THESE
from directorofme_auth.resources.group import Group

unscoped_identity = scoped_identity(app)
authorized_for_read_identity = scoped_identity(app, real_db.Model.__scope__.read)
authorized_for_all_identity = scoped_identity(
    app, real_db.Model.__scope__.read, real_db.Model.__scope__.write, real_db.Model.__scope__.delete,
    groups_module.admin
)

@pytest.fixture
def group(db):
    member = models.Group(display_name="Child",
                          type=groups_module.GroupTypes.data,
                          read=(groups_module.user.name,),
                          write=(groups_module.admin.name,),
                          delete=(group_of_one.name,))
    member_of = models.Group(display_name="Parent",
                             type=groups_module.GroupTypes.data,
                             read=(groups_module.user.name,),
                             write=(groups_module.admin.name,),
                             delete=(group_of_one.name,))
    group = models.Group(display_name="Test",
                         type=groups_module.GroupTypes.data,
                         read=(groups_module.user.name,),
                         write=(groups_module.admin.name,),
                         delete=(group_of_one.name,),
                         members=[member],
                         member_of=[member_of])
    db.session.add(group)
    with real_db.Model.disable_permissions():
        db.session.commit()
        group = existing(group)

    assert real_db.Model.permissions_enabled(), "permissions are enabled"
    yield group

class TestGroup:
    def test__get(self, test_client, group):
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get("/api/-/auth/groups/{}".format(group.name))
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "unauthorized access returns a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("/api/-/auth/groups/{}".format(group.name))
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "successful select returns a 200"

        assert dict_from_response(response) == {
            "id": str(group.id),
            "name": group.name,
            "type": group.type.name,
            "display_name": group.display_name,
            "created": group.created.replace(tzinfo=timezone.utc).isoformat(),
            "updated": group.updated.replace(tzinfo=timezone.utc).isoformat(),
            "scope_name": group.scope_name,
            "scope_permission": group.scope_permission,

            "_links": {
                "self": "/api/-/auth/groups/{}".format(group.name),
                "collection": "/api/-/auth/groups/",
                "members": "/api/-/auth/groups/{}/members".format(group.name),
                "member_of": "/api/-/auth/groups/{}/member_of".format(group.name)
            }
        }

    def test__put(self, db, test_client, group):
        url = "/api/-/auth/groups/{}".format(group.name)
        put_obj = None
        with token_mock(authorized_for_read_identity) as mock_token:
            put_obj = dict_from_response(test_client.get(url))

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "put", url, data=put_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "unauthorized access returns a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "put", url, data=put_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 403, "read but no write returns a 403"

        db.session.rollback()
        put_obj["scope_name"] = "TEST"
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "put", url, data=put_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "regular update returns a 200"
            assert dict_from_response(response)["scope_name"] == "TEST", "scope updated"

        del put_obj["display_name"]
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "put", url, data=put_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "missing required field returns a 400"

        del put_obj["name"]
        put_obj["display_name"] = "New Display Name"
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "put", url, data=put_obj)
            assert mock_token.called, "mock used"
            assert dict_from_response(response)["display_name"] == "New Display Name", "name updated in response"
            assert dict_from_response(response)["name"] == "d-new-display-name", "name updated in response"
            assert response.status_code == 301, "slug change results in a 301`"
            assert response.headers["Location"].endswith("/d-new-display-name"), "new URL returned in location"


    def test__patch_as_different_from_put(self, db, test_client, group):
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "patch", "/api/-/auth/groups/{}".format(group.name),
                                    data={"scope_name": "TEST"})
            assert response.status_code == 200, "partial update works"
            assert dict_from_response(response)["scope_name"] == "TEST"

    def test__delete(self, db, test_client, group):
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.delete("/api/-/auth/groups/{}".format(group.name))
            assert response.status_code == 404, "not found if no read access"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.delete("/api/-/auth/groups/{}".format(group.name))
            assert response.status_code == 403, "permission denied to delete for read access"

        db.session.rollback()
        with token_mock(authorized_for_all_identity) as mock_token:
            response = test_client.delete("/api/-/auth/groups/{}".format(group.name))
            assert response.status_code == 204, "successful delete returns a 204"

            response = test_client.delete("/api/-/auth/groups/{}".format(group.name))
            assert response.status_code == 404, "object not found after delete"

class TestGroupMembersOrMemberOfList:
    @pytest.mark.parametrize("list_name", ["members", "member_of"])
    def test__get(self, test_client, group, list_name):
        assert real_db.Model.permissions_enabled(), "permissions are enabled"
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get("/api/-/auth/groups/{}/{}".format(group.name, list_name))
            assert response.status_code == 404, "no read access returns 404 for {}".format(list_name)

        with token_mock(authorized_for_read_identity) as mock_token:
            key_name = "member" if list_name == "member_of" else "member_of"
            response = test_client.get("/api/-/auth/groups/{}/{}".format(group.name, list_name))
            assert response.status_code == 200, "successful read returns 200 for {}".format(list_name)
            assert dict_from_response(response) == {
                "collection": [{
                    "id": str(g.id),
                    "name": g.name,
                    "type": g.type.name,
                    "display_name": g.display_name,
                    "created": g.created.replace(tzinfo=timezone.utc).isoformat(),
                    "updated": g.updated.replace(tzinfo=timezone.utc).isoformat(),
                    "scope_name": g.scope_name,
                    "scope_permission": g.scope_permission,

                    "_links": {
                        "self": "/api/-/auth/groups/{}".format(g.name),
                        "collection": "/api/-/auth/groups/",
                        "members": "/api/-/auth/groups/{}/members".format(g.name),
                        "member_of": "/api/-/auth/groups/{}/member_of".format(g.name)
                    }
                } for g in getattr(existing(group), list_name)],
                "_links": {
                    "self": "/api/-/auth/groups/{}/{}".format(group.name, list_name),
                    key_name: "/api/-/auth/groups/{}".format(group.name)
                }
            }

    def test__get_bad_list_name(self, test_client, group):
        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("/api/-/auth/groups/{}/bad".format(group.name))
            response.status_code == 400, "400 returned for bad list_name"

    @pytest.mark.parametrize("list_name", ["members", "member_of"])
    def test__post(self, db, test_client, group, list_name):
        url = "/api/-/auth/groups/{}/{}".format(group.name, list_name)
        new_payload = { "display_name": "Brand New", "type": "data" }

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "post", url, data=new_payload)
            assert response.status_code == 404, "no read access causes a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "post", url, data=new_payload)
            assert response.status_code == 403, "permission denied if no write access"

        db.session.rollback()
        with db.Model.disable_permissions():
            existing_members = getattr(existing(group), list_name)

        names = []
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url, data=new_payload)
            assert response.status_code == 201, "permission denied if no write access"
            assert response.headers["Location"].endswith("/d-brand-new"), "permission denied if no write access"

            names = [c["name"] for c in dict_from_response(response)["collection"]]
            assert names == [c.name for c in existing_members] + ["d-brand-new"], "member is appended"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url, data=new_payload)
            assert response.status_code == 200, "successfully appending existing object returns 200"
            assert names == [c["name"] for c in dict_from_response(response)["collection"]], \
                   "members list is the same after re-appending exising member"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url, data={ "display_name": "incomplete" })
            assert response.status_code == 400, "incomplete data returns 400"

    @pytest.mark.parametrize("list_name", ["members", "member_of"])
    def test__delete(self, db, request_context, test_client, group, list_name):
        url = "/api/-/auth/groups/{}/{}".format(group.name, list_name)

        with db.Model.disable_permissions():
            existing_member = getattr(existing(group), list_name)[0]
            delete_payload = { "display_name": existing_member.display_name, "type": existing_member.type.name }

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "delete", url, data=delete_payload)
            assert response.status_code == 404, "no read access causes a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "delete", url, data=delete_payload)
            assert response.status_code == 403, "permission denied if no write access"

        db.session.rollback()
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "delete", url, data=delete_payload)
            assert response.status_code == 200, "successfully deleting existing object returns 200"
            assert dict_from_response(response)["collection"] == [], "delete removes member from list"

    @pytest.mark.parametrize("list_name", ["members", "member_of"])
    def test__put(self, db, request_context, test_client, group, list_name):
        url = "/api/-/auth/groups/{}/{}".format(group.name, list_name)
        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "put", url, data={ "collection": [] })
            assert response.status_code == 404, "no read access causes a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "put", url, data={ "collection": [] })
            assert response.status_code == 403, "no write access causes a 403"

        db.session.rollback()
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "put", url, data={ "collection": [] })
            assert response.status_code == 200, "successfully deleting existing object returns 200"
            assert dict_from_response(response)["collection"] == [], "put replaces list"

            response = json_request(test_client, "put", url, data={
                "collection": [{ "display_name": "New", "type": "data" },
                               { "display_name": "Child", "type": "data" }]
            })

            assert response.status_code == 200, "successfully deleting existing object returns 200"
            collection = sorted([d["name"] for d in dict_from_response(response)["collection"]])
            assert  collection == ["d-child", "d-new"], "put creates new objects and uses existing ones"

class TestGroups:
    def test__get(self, db, test_client, group):
        url = "/api/-/auth/groups/"
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get(url)
            assert response.status_code == 200, "no permissions returns 200"
            assert dict_from_response(response)["collection"] == [], "no permissions results in empty list"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(url)
            assert response.status_code == 200, "successful get returns 200"

            result = dict_from_response(response)
            result["collection"].sort(key=lambda x: x['name'])
            result["_links"] = comparable_links(result["_links"])

            with db.Model.disable_permissions():
                group = existing(group)
                groups = [group] + group.members + group.member_of

            assert result == {
                "collection": [{
                    "id": str(g.id),
                    "name": g.name,
                    "type": g.type.name,
                    "display_name": g.display_name,
                    "created": g.created.replace(tzinfo=timezone.utc).isoformat(),
                    "updated": g.updated.replace(tzinfo=timezone.utc).isoformat(),
                    "scope_name": g.scope_name,
                    "scope_permission": g.scope_permission,

                    "_links": {
                        "self": "/api/-/auth/groups/{}".format(g.name),
                        "collection": "/api/-/auth/groups/",
                        "members": "/api/-/auth/groups/{}/members".format(g.name),
                        "member_of": "/api/-/auth/groups/{}/member_of".format(g.name)
                    }
                } for g in sorted(groups, key=lambda g: g.name)],
                "page": 1,
                "results_per_page": 50,
                "_links": {
                    "self": (url, "page=1", "results_per_page=50",),
                    "next": (url, "page=1", "results_per_page=50",),
                    "prev": (url, "page=1", "results_per_page=50",),
                }
            }


    def test__get_paginated(self, group, test_client):
        with token_mock(authorized_for_read_identity) as mock_token:
            url = "/api/-/auth/groups/?results_per_page=1"
            all_responses = []
            for i in range(3):
                result = dict_from_response(test_client.get(url))
                url = result["_links"]["next"]
                all_responses += [c["name"] for c in result["collection"]]

            assert sorted(all_responses) == ["d-child", "d-parent", "d-test"], "pagination links work"

    def test__get_params(self, request_context, db, test_client):
        system_group = None
        with db.Model.disable_permissions():
            db.session.add(models.Group(display_name="foo", type=groups_module.GroupTypes.system))
            db.session.add(models.Group(display_name="foo-read",
                                        type=groups_module.GroupTypes.scope,
                                        scope_name="Foo",
                                        scope_permission="read"))
            db.session.commit()

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("/api/-/auth/groups/?type=not-a-thing")
            assert response.status_code == 400, "non-existing type returns a 400"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("/api/-/auth/groups/?type=system")
            assert response.status_code == 200, "existing type has a 200 response code"
            names = [c["name"] for c in dict_from_response(response)["collection"]]
            assert names == ["0-foo"], "only system groups are returned"

            response = test_client.get("/api/-/auth/groups/?scope_name=Foo")
            assert response.status_code == 200, "existing type has a 200 response code"
            names = [c["name"] for c in dict_from_response(response)["collection"]]
            assert names == ["s-foo-read"], "groups associated with scope Foo are returned"

    def test__post(self, db, test_client):
        url = "/api/-/auth/groups/"
        post_data = { "display_name": "test_post", "type": "data" }
        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "post", url, data=post_data)
            assert mock_token.called, "mock used"
            assert response.status_code == 403, "read but no write returns a 403"

        db.session.rollback()
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url, data=post_data)
            assert mock_token.called, "mock used"
            assert response.status_code == 201, "success returns a 201"
            assert response.headers["Location"].endswith("/d-test-post"), "Location header set to new URL"
            assert dict_from_response(response)["name"] == "d-test-post", "post worked!"

        del post_data["display_name"]
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url, data=post_data)
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "missing required field returns a 400"
