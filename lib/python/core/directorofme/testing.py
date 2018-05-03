import json
import contextlib

import pytest
import sqlalchemy

from unittest import mock
from .authorization.orm import Model

# TODO ironically, tests
__all__ = [ "db", "existing", "commit_with_integrity_error", "dict_from_response" ]

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

@contextlib.contextmanager
def token_mock(identity=None, user_claims=None):
    with mock.patch("flask_jwt_extended.view_decorators._decode_jwt_from_request") as jwt_token_mock:
        jwt_token_mock.return_value = { "user_claims": user_claims, "identity": identity }
        yield jwt_token_mock

def dump_and_load(obj, app=None):
    kwargs = { "cls": app.json_encoder } if app is not None else {}
    return json.loads(json.dumps(obj, **kwargs))
