### TODO: Tests
from flask.json import JSONEncoder as FlaskJSONEncoder

class JSONEncoder(FlaskJSONEncoder):
    def default(self, o):
        if hasattr(o, '__json_encode__'):
            return o.__json_encode__()
        return super().default(o)
