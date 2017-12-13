'''
utils.py -- Helper functions and misc bits

@author: Matthew Story <matt@directorof.me>
'''

import functools

__all__ = [ "resource_url" ]

def resource_url(api, *args, **kwargs):
	@functools.wraps(resource_url)
	def real_decorator(cls):
		api.add_resource(cls, *args, **kwargs)
		return cls

	return real_decorator
