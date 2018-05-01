### TODO: Tests
from flask.json import JSONEncoder as FlaskJSONEncoder

class JSONEncoder(FlaskJSONEncoder):
    '''
    JSONEncoder -- provides a protocol allowig objects to define the way they
                   would like to be encoded by the JSON serializer.
    '''
    def default(self, o):
        '''If :param:`o` implements a method :attr:`__json_encode__`, the
           method is called and the return value of that method is returned.

           :param object o: to be decoded.
        '''
        if hasattr(o, '__json_encode__'):
            return o.__json_encode__()
        return super().default(o)
