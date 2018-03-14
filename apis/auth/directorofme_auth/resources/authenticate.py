import flask
import itertools
import functools

from requests_oauthlib import OAuth2Session
from flask_restful import Resource, fields, marshal_with, abort, reqparse
from oauthlib.oauth2 import OAuth2Error

from directorofme.authorization import session, groups
from directorofme_flask_restful import resource_url

from . import api, config
from ..models import Profile
from ..exceptions import EmailNotVerified, NoUserForEmail

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
            email = self.get_verified_email(client)
            session = self.make_session_from_email(email)
            return session
            return { "email": email }
        except OAuth2Error as e:
            return abort(400, message=str(e))
        except EmailNotVerified as e:
            return abort(400, message="Email ({}) not verified".format(str(e)))
        except NoUserForEmail as e:
            return abort(404, message="No user associated with email ({})".format(email))

    @staticmethod
    def get_verified_email(client):
        token = client.session.fetch_token(client.token_url, client_secret=client.client_secret,
                                           authorization_response=flask.request.url)
        email, verified = client.confirm_email(token)
        if not verified:
            raise EmailNotVerified(email)

        return email

    @staticmethod
    def make_session_from_email(email):
        ### TODO: build session token, set headers/cookies and return success
        profile = Profile.query.filter(Profile.email == email).first()
        if not profile:
            raise NoUserForEmail(email)

        primary_groups = [ profile.group_of_one ]
        for license in profile.licenses:
            primary_groups += license.groups
        ### XXX: mix in app groups

        return session.Session(
            id=None, # XXX: get_jti
            environment=profile.preferences or {},
            profile=session.SessionProfile.from_conforming_type(profile),
            groups=[groups.Group.from_conforming_type(g) for group in primary_groups for g in group.expand()],
            app=None, # XXX: App
        )

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

