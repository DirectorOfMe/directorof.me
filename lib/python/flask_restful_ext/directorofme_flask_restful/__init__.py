'''
__init__.py -- The directorofme_flask_restful package, extending the
               functionality of flask_restful.

@author: Matthew Story <matt@directorof.me>
'''

from . import fields
from .utils import resource_url

__all__ = [ "fields", "resource_url" ]
