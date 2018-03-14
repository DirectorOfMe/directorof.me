import flask
import functools

from requests_oauthlib import OAuth2Session
from flask_restful import Resource, fields, marshal_with, abort, reqparse
from oauthlib.oauth2 import OAuth2Error

from directorofme_flask_restful import resource_url

from . import api, config

### TODO: offline for integrations, but not for auth
def with_service_client(fn):
    @functools.wraps(fn)
    def inner(obj, service, *args, **kwargs):
        client = None
        if service == "google":
            client = Google()
        else:
            return abort(404, message="no oauth service named {}".format(service))

        return fn(obj, client, *args, **kwargs)

    return inner

@resource_url(api, "/oauth/<string:service>", endpoint="oauth_api")
class OAuth(Resource):
    @with_service_client
    def get(self, client):
        url = client.session.authorization_url(client.auth_url, **client.auth_kwargs)[0]
        return { "auth_url": url }, 302, { "Location": url }


@resource_url(api, "/oauth/<string:service>/callback", endpoint="oauth_callback_api")
class OAuthCallback(Resource):
    @with_service_client
    def get(self, client):
        parser = reqparse.RequestParser()
        parser.add_argument("error", type="string", help="error message")
        args = parser.parse_args()

        if args["error"]:
            return abort(400, message=error)

        try:
            email, verified = client.confirm_email(
                client.session.fetch_token(
                    client.token_url,
                    client_secret=client.client_secret,
                    authorization_response=flask.request.url))
            if not verified:
                abort(400, message="{} hasn't verified your email ({})".format(service, email))

            return { "email": email }

        except OAuth2Error as e:
            return abort(400, message=str(e))


class Client:
    def __init__(self, service, client_id, client_secret, auth_url, token_url, auth_kwargs, session_kwargs):
        self.service = service
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.auth_kwargs = auth_kwargs

        self.session = OAuth2Session(
            self.client_id,
            redirect_uri=api.url_for(OAuthCallback, api_version="-", service=self.service, _external=True),
            **session_kwargs
        )

    def confirm_email(self, token=None):
        raise NotImplementedError("Subclass must implement")


class Google(Client):
    def __init__(self):
        super().__init__(
            "google", config.get("GOOGLE_CLIENT_ID"), config.get("GOOGLE_CLIENT_SECRET"),
            config.get("GOOGLE_AUTH_URL"), config.get("GOOGLE_TOKEN_URL"), { "prompt": "select_account" },
            { "scope": [ "https://www.googleapis.com/auth/userinfo.email",
                         "https://www.googleapis.com/auth/userinfo.profile" ]
            }
        )

    def confirm_email(self, token=None):
        id_ = self.session.get("https://www.googleapis.com/oauth2/v3/tokeninfo",
                               params={"id_token": token.get("id_token")}).json()
        return id_["email"], id_["email_verified"]

