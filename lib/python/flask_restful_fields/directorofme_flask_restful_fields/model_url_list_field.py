# hack to get around issue #714 in flask-restful
class ModelUrlListField(fields.List):
    def __init__(self, *url_args, **url_kwargs):
        return super(ModelUrlListField, self).__init__(fields.Url(*url_args, **url_kwargs))

    def format(self, model_list):
        return super(ModelUrlListField, self).format([fields.to_marshallable_type(val) for val in model_list])
### /XXX

