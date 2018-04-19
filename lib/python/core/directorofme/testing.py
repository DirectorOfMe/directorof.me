import json

import pytest
import sqlalchemy

from .authorization.orm import Model

# TODO ironically, tests
__all__ = [ "DBFixture", "existing", "commit_with_integrity_error", "dict_from_response" ]

class DBFixture:
	def __init__(self, real_db):
		self.real_db = real_db
		self.to_cleanup = []

	def track_for_deletion(self, session):
		self.to_cleanup += session.new

	def fixture(self, fixture_name="db"):
		def inner(request):
			sqlalchemy.event.listen(
				self.real_db.session,
				"before_commit",
				self.track_for_deletion)

			yield self.real_db

			try:
				self.real_db.session.rollback()
				for obj in self.to_cleanup:
					try:
						self.real_db.session.delete(obj)
					except sqlalchemy.exc.InvalidRequestError:
						pass
				self.real_db.session.commit()
			finally:
				self.to_cleanup = []
				sqlalchemy.event.remove(
					self.real_db.session,
					"before_commit",
					self.track_for_deletion)

		inner.__name__ = fixture_name
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


def disable_permissions():
    def false():
        return False

    original_checker = Model.permissions_enabled
    Model.permissions_enabled = false
    yield
    Model.original_checker= original_checker
