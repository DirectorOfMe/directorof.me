from flask_restful import fields

from .. import api

### XXX: move these
import functools
def resource_url(*args, **kwargs):
	@functools.wraps(resource_url)
	def real_decorator(cls):
		api.add_resource(cls, *args, **kwargs)
		return cls

	return real_decorator

# hack to get around issue #714 in flask-restful
class ModelUrlListField(fields.List):
    def __init__(self, *url_args, **url_kwargs):
        return super(ModelUrlListField, self).__init__(fields.Url(*url_args, **url_kwargs))

    def format(self, model_list):
        return super(ModelUrlListField, self).format([fields.to_marshallable_type(val) for val in model_list])
### /XXX

from .group import Group
from .profile import Profile
from .app import App
from .session import Session

__all__ = [ "Session", "Group", "Profile", "App" ]
