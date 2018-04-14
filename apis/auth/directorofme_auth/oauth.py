from flask_restful import reqparse
from requests_oauthlib import OAuth2Session

from . import config
from directorofme.authorization.exceptions import MisconfiguredAuthError

__all__ = [ "Client", "Google" ]


### TODO: Factor into shared library for use by many backend apps
###       When you do this, SECRET will only be needed by the auth service
class ClientMeta(type):
    '''Meta class, used to pick which client to use'''
    registry = {}

    def __new__(cls, object_or_name, bases, __dict__):
        built = super().__new__(cls, object_or_name, bases, __dict__)

        name = __dict__.get("name")
        if name is not None:
            if name in cls.registry:
                raise TypeError("Class already registered for {} ({})".format(name, built))
            cls.registry[name] = built

        return built

class Client(metaclass=ClientMeta):
    '''Generic OAuth client to hold state for all requests'''
    # protocol
    name = None

    @classmethod
    def client_by_name(cls, name):
        return type(cls).registry.get(name)

    def __init__(self, callback_url, client_id, client_secret, auth_url, token_url, auth_kwargs,
                 session_kwargs, offline=False):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.auth_kwargs = auth_kwargs
        self.offline = offline

        self.session = OAuth2Session(self.client_id, redirect_uri=callback_url, **session_kwargs)

    def __getattr__(self, name):
            return getattr(self.session, name)

    def confirm_email(self, token=None):
        raise NotImplementedError("Subclass must implement")

    def check_callback_request_for_errors(self, request):
        raise NotImplementedError("Subclass must implement")

    def authorization_url(self):
        return self.session.authorization_url(self.auth_url, **self.auth_kwargs)[0]

    def fetch_token(self, resp_url):
        if self.client_secret is None:
            raise MisconfiguredAuthError("May only fetch token if secret is present")
        return self.session.fetch_token(self.token_url, client_secret=self.client_secret,
                                        authorization_response=resp_url)


class Google(Client):
    '''Google OAuth client, pulling from flask config'''
    name = "google"

    def __init__(self, callback_url, offline=False):
        auth_kwargs = { "prompt": "consent" }
        if offline:
            auth_kwargs["access_type"] ="offline"

        super().__init__(
            callback_url,
            config.get("GOOGLE_CLIENT_ID"),
            config.get("GOOGLE_CLIENT_SECRET"),
            config.get("GOOGLE_AUTH_URL"),
            config.get("GOOGLE_TOKEN_URL"),
            auth_kwargs,
            { "scope": [ "https://www.googleapis.com/auth/userinfo.email",
                         "https://www.googleapis.com/auth/userinfo.profile" ]
            },
            offline=offline
        )

    def confirm_email(self, token=None):
        params = { "id_token": token.get("id_token") }
        id_ = self.get("https://www.googleapis.com/oauth2/v3/tokeninfo", params=params).json()
        return id_["email"], id_["email_verified"]

    def check_callback_request_for_errors(self, request):
        return request.args.get("error")
