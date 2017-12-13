from .. import api

### XXX: move this
import functools
def resource_url(*args, **kwargs):
	@functools.wraps(resource_url)
	def real_decorator(cls):
		api.add_resource(cls, *args, **kwargs)
		return cls

	return real_decorator
### /XXX


from .group import Group
from .profile import Profile
from .app import App, InstalledApp
from .session import Session
from .license import License

__all__ = [ "Session", "Group", "Profile", "App", "License" ]
