'''
model_url_list.py -- ModelUrlList

@author: Matthew Story <matt@directorof.me>

XXX: Remove when flask_restful issue #714 is merged to a stable release
'''
from flask_restful import fields

class ModelUrlList(fields.List):
    def __init__(self, *url_args, **url_kwargs):
        return super().__init__(fields.Url(*url_args, **url_kwargs))

    def format(self, model_list):
        return super().format(
            [fields.to_marshallable_type(val) for val in model_list]
        )
