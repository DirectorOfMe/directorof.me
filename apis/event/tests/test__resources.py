import uuid
import json
import copy

from urllib.parse import urlparse
from datetime import timezone

import pytest

from unittest import mock

from directorofme.authorization import groups, session
from directorofme_event import app, spec, db as real_db
from directorofme_event.models import Event, EventType
from directorofme.testing import dict_from_response, token_mock, existing, dump_and_load, comparable_links,\
                                 scoped_identity, group_of_one, json_request

unscoped_identity = scoped_identity(app)
authorized_for_read_identity = scoped_identity(app, real_db.Model.__scope__.read)
authorized_for_all_identity = scoped_identity(
    app, real_db.Model.__scope__.read, real_db.Model.__scope__.write, real_db.Model.__scope__.delete,
    groups.admin
)

@pytest.fixture
def test_client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def event_type(db):
    with app.test_request_context():
        event_type = EventType(name="Test Event Type",
                               desc="A Test",
                               data_schema={ "a": "schema" },
                               read=(groups.user.name,),
                               write=(groups.admin.name,),
                               delete=(group_of_one.name,))
        potential_conflict = EventType(name="Test Conflict",
                                       desc="Test",
                                       data_schema={ "a": "schema" },
                                       read=(groups.user.name,),
                                       write=(groups.admin.name,),
                                       delete=(group_of_one.name,))


        db.session.add(event_type)
        db.session.add(potential_conflict)
        with real_db.Model.disable_permissions():
            db.session.commit()
            obj = existing(event_type)

    yield obj


@pytest.fixture
def event(db):
    with app.test_request_context():
        event_type = EventType(name="Test Event Type",
                               desc="A Test",
                               data_schema={ "a": "schema" },
                               read=(groups.user.name,),
                               write=(groups.admin.name,),
                               delete=(group_of_one.name,))
        event = Event(event_type=event_type,
                      data={ "data": "test" },
                      read=(groups.user.name,),
                      write=(groups.admin.name,),
                      delete=(group_of_one.name,))

        db.session.add(event_type)
        db.session.add(event)
        with real_db.Model.disable_permissions():
            db.session.commit()
            obj = existing(event)

    yield obj

class TestEventType:
    def test__get(self, test_client, event_type):
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get("/api/-/event/event_types/{}".format(event_type.slug))
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "unauthorized access returns a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("/api/-/event/event_types/{}".format(event_type.slug))
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "successful select returns a 200"

        assert dict_from_response(response) == {
            "name": event_type.name,
            "slug": event_type.slug,
            "created": event_type.created.replace(tzinfo=timezone.utc).isoformat(),
            "updated": event_type.updated.replace(tzinfo=timezone.utc).isoformat(),
            "desc": event_type.desc,
            "data_schema": event_type.data_schema,
            "_links": {
                "self": "/api/-/event/event_types/{}".format(event_type.slug),
                "collection": "/api/-/event/event_types/"
            }
        }, "response body is correct"

    def test__put(self, test_client, event_type):
        url = "/api/-/event/event_types/{}".format(event_type.slug)
        event_type_client_obj = None

        with token_mock(authorized_for_read_identity) as mock_token:
            event_type_client_obj = dict_from_response(test_client.get(url))

        missing_desc = copy.deepcopy(event_type_client_obj)
        del missing_desc["desc"]
        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "put", url, data=missing_desc)
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "missing required field returns a 400"

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "put", url, data=event_type_client_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "no read access returns a 404"

        event_type_client_obj["desc"] = "Updated"
        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "put", url, data=event_type_client_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 403, "no update access returns a 403"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "put", url, data=event_type_client_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "scoped read + object write updates"

            response_dict = dict_from_response(response)
            assert response_dict["desc"] == "Updated", "description is updated"
            assert response_dict["created"] == event_type_client_obj["created"], "created time is not modified"
            assert response_dict["updated"] > event_type_client_obj["updated"], "updated time is modified"

        event_type_client_obj["name"] = "I am a different name"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "put", url, data=event_type_client_obj)
            assert mock_token.called, "mock used"
            assert response.status_code == 301, "when slug is changedl, a 301 is returned"
            assert response.headers.get('Location').endswith("/api/-/event/event_types/i-am-a-different-name"), \
                "Location header is set to new URL"

            assert dict_from_response(response)["slug"] == "i-am-a-different-name", "slug updated"

    def test__patch(self, test_client, event_type):
        url = "/api/-/event/event_types/{}".format(event_type.slug)

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "patch", url, data={})
            assert mock_token.called, "mock used"
            assert response.status_code == 404, \
                "no read access returns a 404 (missing fields aren't a validation error"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "patch", url, data={"desc": "Updated"})
            assert mock_token.called, "mock used"
            assert response.status_code == 403, \
                "no read access returns a 404 (missing fields aren't a validation error"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "patch", url, data={"data_schema": "abcdefg"})
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "invalid type returns 400"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "patch", url, data={"name": "New Name"})
            assert mock_token.called, "mock used"
            assert response.status_code == 301, "new slug returns a 301"

        url = "/api/-/event/event_types/new-name"
        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "patch", url, data={"name": "Test Conflict"})
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "duplicate slug on update returns 400"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "patch", url, data={"desc": "Updated"})
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "partial update works"
            assert dict_from_response(response)["desc"] == "Updated", "partial update works"

    def test__delete(self, test_client, event_type):
        url = "/api/-/event/event_types/{}".format(event_type.slug)
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.delete(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "no read access returns a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.delete(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 403, "no permission returns a 403"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = test_client.delete(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 204, "successful delete"
            assert test_client.get(url).status_code == 404, "resource not found after successful delete"


@pytest.fixture
def event_type_collection(db):
    with app.test_request_context():
        collection = []
        for i in range(51):
            collection.append(EventType(name="Test Event Type -- {}".format(i),
                                        desc="A Test",
                                        data_schema={ "a": "schema" },
                                        read=(groups.user.name,),
                                        write=(groups.admin.name,),
                                        delete=(group_of_one.name,)))
        db.session.add_all(collection)
        with real_db.Model.disable_permissions():
            db.session.commit()
            objs = EventType.query.all()

    yield objs


class TestEventTypes:
    def test__get(self, test_client, event_type_collection):
        url = "/api/-/event/event_types/"
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "with no access a 200 is returned"

            response_dict = dict_from_response(response)
            response_dict["_links"] = comparable_links(response_dict["_links"])
            assert response_dict == {
                "page": 1,
                "results_per_page": 50,
                "collection": [],
                "_links": {
                    "self": (url, "page=1", "results_per_page=50"),
                    "next": (url, "page=1", "results_per_page=50"),
                    "prev": (url, "page=1", "results_per_page=50"),
                }
            }, "empty collection response is correct"

        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get("{}?results_per_page=abc".format(url))
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "if args are malformed, 400 is returned"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "with permissions returns a 200"

            response_dict = dict_from_response(response)
            assert len(response_dict["collection"]) == 50, "full page of results returned"
            slugs = {x["slug"] for x in response_dict["collection"]}

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(response_dict["_links"]["next"])
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "with permissions returns a 200"

            response_dict = dict_from_response(response)
            assert len(response_dict["collection"]) == 1, "one result returned"
            assert comparable_links(response_dict["_links"]) == {
                "self": (url, "page=2", "results_per_page=50"),
                "next": (url, "page=2", "results_per_page=50"),
                "prev": (url, "page=1", "results_per_page=50"),
            }, "links correct for last page"

            slugs |= {x["slug"] for x in response_dict["collection"]}
            assert slugs == {x.slug for x in event_type_collection}, "all objects returned"

            response = test_client.get("{}?results_per_page=10".format(url))
            assert len(dict_from_response(response)["collection"]) == 10, "results_per_page works"


    def test__post(self, test_client):
        url = "/api/-/event/event_types/"

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "post", url, data={})
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "invalid object returns a 400"

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "post", url, data={"name": "A", "desc": "B", "data_schema": {}})
            assert mock_token.called, "mock used"
            assert response.status_code == 403, "valid post without permission returns 403"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url, data={"name": "A", "desc": "B", "data_schema": {}})

            assert mock_token.called, "mock used"
            assert response.status_code == 201, "entity created and status 201 returned"
            assert response.headers.get("Location").endswith("/api/-/event/event_types/a"),\
                   "location header correctly set"
            assert dict_from_response(response)["slug"] == "a", "slug set by creation"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url, data={"name": "A", "desc": "B", "data_schema": {}})
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "duplicate slug returns 400"

class TestEvent:
    def test__get(self, test_client, event):
        url = "/api/-/event/events/{}".format(str(event.id))
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "can't find becuase of permission returns a 404"

        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get("/api/-/event/events/abcd")
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "poorly formed UUID returns a 400"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "existing event returns 200"
            assert dict_from_response(response) == {
                "id": str(event.id),
                "created": event.created.replace(tzinfo=timezone.utc).isoformat(),
                "updated": event.updated.replace(tzinfo=timezone.utc).isoformat(),
                "event_time": event.event_time.replace(tzinfo=timezone.utc).isoformat(),
                "event_type_slug": "test-event-type",
                "data": event.data,

                "_links": {
                    "self": url,
                    "collection": "/api/-/event/events/",
                    "event_type": "/api/-/event/event_types/test-event-type"
                }
            }, "response well formed"

    def test__delete(self, test_client, event):
        url = "/api/-/event/events/{}".format(event.id)
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.delete(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "no read access returns a 404"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.delete(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 403, "no permission returns a 403"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = test_client.delete(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 204, "successful delete"
            assert test_client.get(url).status_code == 404, "resource not found after successful delete"


@pytest.fixture
def event_collection(db):
    with app.test_request_context():
        event_type = EventType(name="Test Event Type",
                               desc="A Test",
                               data_schema={ "a": "schema" },
                               read=(groups.user.name,),
                               write=(groups.admin.name,),
                               delete=(group_of_one.name,))

        event_type_1 = EventType(name="Test Event Type 1",
                               desc="A Test",
                               data_schema={ "a": "schema" },
                               read=(groups.user.name,),
                               write=(groups.admin.name,),
                               delete=(group_of_one.name,))
        collection = []
        for i in range(50):
            collection.append(Event(event_type=event_type, data={ "data": "set" },
                                    read=(groups.user.name,),
                                    write=(groups.admin.name,),
                                    delete=(group_of_one.name,)))

        collection.append(Event(event_type=event_type_1, data={ "data": "set" },
                                read=(groups.user.name,),
                                write=(groups.admin.name,),
                                delete=(group_of_one.name,)))

        db.session.add(event_type)
        db.session.add(event_type_1)
        db.session.add_all(collection)
        with real_db.Model.disable_permissions():
            db.session.commit()
            objs = Event.query.all()

    yield objs


class TestEvents:
    def test__get(self, test_client, event_collection):
        url = "/api/-/event/events/"
        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "with no access a 200 is returned"

            response_dict = dict_from_response(response)
            response_dict["_links"] = comparable_links(response_dict["_links"])
            assert response_dict == {
                "results_per_page": 50,
                "collection": [],
                "_links": {
                    "self": (url, "results_per_page=50"),
                    "next": (url, "results_per_page=50"),
                    "prev": (url, "results_per_page=50"),
                }
            }, "empty collection response is correct"

        with token_mock(unscoped_identity) as mock_token:
            response = test_client.get("{}?results_per_page=abc".format(url))
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "if args are malformed, 400 is returned"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(url)
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "with permissions returns a 200"

            response_dict = dict_from_response(response)
            assert len(response_dict["collection"]) == 50, "full page of results returned"
            ids = {x["id"] for x in response_dict["collection"]}

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(response_dict["_links"]["next"])
            assert mock_token.called, "mock used"
            assert response.status_code == 200, "with permissions returns a 200"

            response_dict = dict_from_response(response)
            assert len(response_dict["collection"]) == 1, "one result returned"
            assert comparable_links(response_dict["_links"]) == {
                "self": (url, "results_per_page=50", "since_id={}".format(str(event_collection[-2].id))),
                "prev": (url, "max_id={}".format(str(event_collection[-2].id)), "results_per_page=50"),
                "next": (url, "results_per_page=50", "since_id={}".format(str(event_collection[-1].id))),
            }, "links correct for last page"

            ids |= {x["id"] for x in response_dict["collection"]}
            assert ids == {str(x.id) for x in event_collection}, "all objects returned"

            response = test_client.get("{}?results_per_page=10".format(url))
            assert len(dict_from_response(response)["collection"]) == 10, "results_per_page works"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(response_dict["_links"]["prev"])
            assert mock_token.called, "mock used"
            assert len(dict_from_response(response)["collection"]) == 50, "full page of results returned"


        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get(
                "{}?results_per_page=10&max_id={}".format(url, str(event_collection[-1].id)))
            assert mock_token.called, "mock used"

            response_dict = dict_from_response(response)
            ids = [i["id"] for i in response_dict["collection"]]
            assert ids[-1] == str(event_collection[-1].id), "max_id is the last item in the collection"

            response = test_client.get(response_dict["_links"]["prev"])
            ids = [i["id"] for i in dict_from_response(response)["collection"]] + ids
            assert ids == [str(i.id) for i in event_collection[-20:]], "pages are contiguous"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("{}?event_type_slug=test-event-type-1".format(url))
            assert mock_token.called, "mock used"
            assert len(dict_from_response(response)["collection"]) == 1, "filtered down to one event"

    def test__get_with_bad_max_id_or_since_id(self, test_client):
        with token_mock(authorized_for_read_identity) as mock_token:
            response = test_client.get("/api/-/event/events/?since_id={}".format(str(uuid.uuid1())))
            assert mock_token.called, "mock used"
            assert response.status_code == 409, "invalid since_id returns 409"

            response = test_client.get("/api/-/event/events/?max_id={}".format(str(uuid.uuid1())))
            assert mock_token.called, "mock used"
            assert response.status_code == 409, "invalid max_id returns 409"

    def test__post(self, test_client, event_type):
        url = "/api/-/event/events/"

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "post", url, data={})
            assert mock_token.called, "mock used"
            assert response.status_code == 400, "invalid object returns a 400"

        with token_mock(unscoped_identity) as mock_token:
            response = json_request(test_client, "post", url,
                                    data={"event_type_slug": event_type.slug, "data": { "test": "data" }})
            assert mock_token.called, "mock used"
            assert response.status_code == 404, "404 if event_type can't be selected"

        with token_mock(authorized_for_read_identity) as mock_token:
            response = json_request(test_client, "post", url,
                                    data={"event_type_slug": event_type.slug, "data": { "test": "data" }})
            assert mock_token.called, "mock used"
            assert response.status_code == 403, "valid post without permission returns 403"

        with token_mock(authorized_for_all_identity) as mock_token:
            response = json_request(test_client, "post", url,
                                    data={"event_type_slug": event_type.slug, "data": { "test": "data" }})

            assert mock_token.called, "mock used"
            assert response.status_code == 201, "entity created and status 201 returned"
            assert response.headers.get("Location").endswith("/api/-/event/events/{}".format(
                        str(dict_from_response(response)["id"])
                   )), "location header correctly set"


def test__Spec_get(test_client):
    response = test_client.get("/api/-/event/swagger.json")
    assert response.status_code == 200, "swagger endpoint returns 200"
    assert dict_from_response(response) == dump_and_load(spec.to_dict()), "results are produced from the spec"
