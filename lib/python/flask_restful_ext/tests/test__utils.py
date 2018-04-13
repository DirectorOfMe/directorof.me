import json
from flask_restful import Resource

from directorofme_flask_restful import resource_url

def test__resource_url(app, api):
    @resource_url(api, "/endpoint", endpoint="endpoint")
    class Endpoint(Resource):
        def get(self):
            return { "hello": "world" }


    with app.test_client() as client:
        resp = client.get("/endpoint")
        assert json.loads(resp.get_data().decode("utf-8")) == { "hello": "world" }
