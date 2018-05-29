import uuid
import json
import contextlib

import pytest
import sqlalchemy

from unittest import mock
from .authorization.orm import Model
from .authorization import groups

# TODO ironically, tests
__all__ = [ "db", "existing", "commit_with_integrity_error", "dict_from_response", "dump_and_load",
            "comparable_links", "profile_id", "group_of_one", "unscoped_identity", "scoped_identity",
            "token_mock" ]

def db(real_db):
    def inner():
        yield real_db

        real_db.session.rollback()
        for table in reversed(Model.metadata.sorted_tables):
            real_db.engine.execute(table.delete())
        real_db.session.commit()

    inner.__name__ = "db"
    return inner

def commit_with_integrity_error(db, *objs):
    db.session.add_all(objs)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.commit()
    db.session.rollback()


def existing(model, query_on="id"):
    return model.__class__.query.filter(
        getattr(model.__class__, query_on) == getattr(model, query_on)
    ).first()


def dict_from_response(response):
    return json.loads(response.get_data().decode("utf-8"))

def json_request(client, method, url, data):
    return getattr(client, method)(url, data=json.dumps(data), content_type="application/json")


def dump_and_load(obj, app=None):
    kwargs = { "cls": app.json_encoder } if app is not None else {}
    return json.loads(json.dumps(obj, **kwargs))

def comparable_links(links):
    ret_links = {}
    for k,v in links.items():
        base, qs = v.split("?")
        ret_links[k] = (base,) + tuple(sorted(qs.split("&")))

    return ret_links

profile_id = uuid.uuid1()
group_of_one = groups.Group(display_name=str(profile_id), type=groups.GroupTypes.data)

def unscoped_identity(app):
    return {
        "profile": { "id": str(profile_id), "email": "test@example.com" },
        "groups": [
            dump_and_load(groups.everybody, app),
            dump_and_load(groups.user, app),
            dump_and_load(group_of_one, app)
        ],
        "app": { "id": str(uuid.uuid1()), "app_id": str(uuid.uuid1()), "app_slug": "event", "config": {} },
        "default_object_perms": {
            "read": [ group_of_one.name ], "write": [ group_of_one.name ], "delete": [ group_of_one.name ]
        },
        "environment": {}
    }

def scoped_identity(app, *groups):
    scoped = unscoped_identity(app)
    scoped["groups"] += dump_and_load(groups, app)
    return scoped


@contextlib.contextmanager
def token_mock(identity=None, user_claims=None):
    with mock.patch("flask_jwt_extended.view_decorators._decode_jwt_from_request") as jwt_token_mock:
        jwt_token_mock.return_value = { "user_claims": user_claims, "identity": identity }
        yield jwt_token_mock
