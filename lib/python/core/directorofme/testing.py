import pytest
import sqlalchemy

__all__ = [ "DBFixture" ]
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
