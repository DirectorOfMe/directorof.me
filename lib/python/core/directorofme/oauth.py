from furl import furl
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import OAuth2Error

from directorofme.registry import RegisterByName
from directorofme.authorization.exceptions import MisconfiguredAuthError

__all__ = [ "Client", "Google", "Slack" ]


### TODO: Factor into shared library for use by many backend apps
###       When you do this, SECRET will only be needed by the auth service
class Client(RegisterByName, metaclass=RegisterByName.make_registrymetaclass()):
    '''Generic OAuth client to hold state for all requests'''
    def __init__(self, callback_url, client_id, auth_url, token_url, auth_kwargs,
                 session_kwargs, client_secret=None, offline=False, state=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.auth_kwargs = auth_kwargs
        self.offline = offline

        self.session = OAuth2Session(self.client_id, redirect_uri=callback_url, state=state, **session_kwargs)

    def __getattr__(self, name):
        return getattr(self.session, name)

    def confirm_identity(self, token=None):
        raise NotImplementedError("Subclass must implement")

    def check_callback_request_for_errors(self, request):
        return request.args.get("error")

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

    def __init__(self, config, callback_url=None, scopes=tuple(), offline=False, state=None):
        auth_kwargs = { "prompt": "consent" }
        if offline:
            auth_kwargs["access_type"] ="offline"

        scopes = scopes or [ "https://www.googleapis.com/auth/userinfo.email",
                             "https://www.googleapis.com/auth/userinfo.profile" ]
        super().__init__(
            callback_url,
            config.get("GOOGLE_CLIENT_ID"),
            config.get("GOOGLE_AUTH_URL"),
            config.get("GOOGLE_TOKEN_URL"),
            auth_kwargs,
            { "scope": scopes },
            config.get("GOOGLE_CLIENT_SECRET"),
            offline=offline,
            state=state
        )

    def confirm_identity(self, token=None):
        params = { "id_token": token.get("id_token") }
        id_ = self.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
        return id_["email"], id_["email_verified"], id_["name"]


class Slack(Client):
    name = "slack"

    def __init__(self, config, callback_url=None, scopes=("identity.basic", "identity.email"),
                 state=None, **kwargs):
        self.app_id = config.get("SLACK_APP_ID")
        super().__init__(
            callback_url,
            config.get("SLACK_CLIENT_ID"),
            config.get("SLACK_AUTH_URL"),
            config.get("SLACK_TOKEN_URL"),
            {},
            { "scope": ",".join(scopes) },
            config.get("SLACK_CLIENT_SECRET"),
            state=state
        )

    def confirm_identity(self, token=None):
        response = self.get("https://slack.com/api/users.identity").json()
        if response["ok"]:
            email = response["user"].get("email")
            return email, bool(email), response["user"].get("name")

        raise OAuth2Error(response.get("error", "Error connecting to slack"))

    def app_url(self):
        return furl("https://slack.com/app_redirect").add({"app": self.app_id}).url
