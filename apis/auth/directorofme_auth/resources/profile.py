@spec.register_resource
@api.resource("/apps/<string:email>", endpoint="profile_api")
class Profile(Resource):
    """
    A endpoint for retrieving and manipulating applications
    """
    def get(
