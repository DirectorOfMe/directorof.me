from directorofme.testing import dump_and_load
from directorofme_auth import spec

def test__Spec_get(test_client):
    response = test_client.get("/api/-/auth/swagger.json")
    assert response.status_code == 200, "swagger endpoint returns 200"
    assert response.get_json() == dump_and_load(spec.to_dict()), "results are produced from the spec"
