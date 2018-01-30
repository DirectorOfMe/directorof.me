import json

import pytest

from directorofme.json import JSONEncoder

class Implements:
    def __json_encode__(self):
        return 'hi'

class TestJSONEncoder:
    def test__default(self):
        with pytest.raises(TypeError):
            JSONEncoder().default({ "does not": "implement" })

        assert JSONEncoder().default(Implements()) == 'hi'

    def test__dumps(self):
        assert json.dumps(Implements(), cls=JSONEncoder) == '"hi"',\
               "custom encoder works"

        value = json.dumps({ "foo": Implements(), "bar": 1 }, cls=JSONEncoder)
        assert value == json.dumps({ "foo": "hi", "bar": 1}),\
               "dumps works with encoder protocol"
