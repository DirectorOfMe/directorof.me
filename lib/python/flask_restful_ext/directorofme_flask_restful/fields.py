'''
fields.py -- ModelUrlList, AttributedUrl

@author: Matthew Story <matt@directorof.me>

XXX: Remove when flask_restful issue #714 is merged to a stable release
'''
from flask_restful import fields

__all__ = [ "AttributedUrl", "ModelUrlList" ]

class ModelUrlList(fields.List):
    def __init__(self, *url_args, **url_kwargs):
        return super().__init__(fields.Url(*url_args, **url_kwargs))

    def format(self, model_list):
        return super().format(
            [fields.to_marshallable_type(val) for val in model_list]
        )


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
