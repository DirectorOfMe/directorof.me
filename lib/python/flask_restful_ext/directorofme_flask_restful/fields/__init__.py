'''
fields/__init__.py -- Additional flask_restful fields.

@author: Matthew Story <matt@directorof.me>
'''

### ORDER MATTERS
from .attributed_uri import AttributedUrl
from .model_url_list import ModelUrlList

__all__ = [ "AttributedUrl", "ModelUrlList" ]
