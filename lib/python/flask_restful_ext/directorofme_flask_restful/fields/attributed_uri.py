'''
attributed_uri.py -- AttributedUrl

@author: Matthew Story <matt@directorof.me>

XXX: Remove when flask_restful issue #702 is merged to a stable release
'''
from flask_restful import fields

__all__ = [ "AttributedUrl" ]

class AttributedUrl(fields.Url):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        ### super super after to reset up shiz
        super(fields.Url, self).__init__(**kwargs)

    def output(self, key, obj):
        ### attribute needs to be super/super called
        return super().output(
            ### super super!
            key, super(fields.Url, self).output(key, obj)
        )
