from .. import api

### XXX: move these
import functools
def resource_url(*args, **kwargs):
	@functools.wraps(resource_url)
	def real_decorator(cls):
		api.add_resource(cls, *args, **kwargs)
		return cls

	return real_decorator
### /XXX

from session import Session
from group import Group
from profile import Profile
from app import App

__all__ = [ "Session", "Group", "Profile", "App" ]
