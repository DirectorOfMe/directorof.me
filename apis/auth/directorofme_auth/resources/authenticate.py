'''
>>> # Credentials you get from registering a new application
>>> client_id = '<the id you get from google>.apps.googleusercontent.com'
>>> client_secret = '<the secret you get from google>'
>>> redirect_uri = 'https://your.registered/callback'

>>> # OAuth endpoints given in the Google API documentation
>>> authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
>>> token_url = "https://www.googleapis.com/oauth2/v4/token"
>>> scope = [
...     "https://www.googleapis.com/auth/userinfo.email",
...     "https://www.googleapis.com/auth/userinfo.profile"
... ]

>>> from requests_oauthlib import OAuth2Session
>>> google = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)

>>> # Redirect user to Google for authorization
>>> authorization_url, state = google.authorization_url(authorization_base_url,
...     # offline for refresh token
...     # force to always make user click authorize
...     access_type="offline", prompt="select_account")
>>> print 'Please go here and authorize,', authorization_url

>>> # Get the authorization verifier code from the callback url
>>> redirect_response = raw_input('Paste the full redirect URL here:')

>>> # Fetch the access token
>>> google.fetch_token(token_url, client_secret=client_secret,
...         authorization_response=redirect_response)

>>> # Fetch a protected resource, i.e. user profile
>>> r = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
>>> print r.content
'''
import flask

from requests_oauthlib import OAuth2Session
from flask_restful import Resource, fields, marshal_with, abort

from directorofme_flask_restful import resource_url

from . import api, config

### TODO: offline for integrations, but not for auth
@resource_url(api, "/authenticate/oauth/<string:service>", endpoint="oauth_api")
class OAuth(Resource):
    def get(self, service):
        client = None

        if service == "google":
            client = Google()
        else:
            return abort(404, message="no oauth service named {}".format(service))

        url = client.auth_redirect()
        return { "auth_url": url }, 302, { "Location": url }


@resource_url(api, "/authenticate/oauth/<string:service>/callback", endpoint="oauth_callback_api")
class OAuthCallback(Resource):
    def get(self, service):
        return { "success": True }


class Google:
    def __init__(self, scope=None):
        self.client_id = config.get("GOOGLE_CLIENT_ID")
        self.client_secret = config.get("GOOGLE_CLIENT_SECRET")
        self.auth_url = config.get("GOOGLE_AUTH_URL")
        self.token_url = config.get("GOOGLE_TOKEN_URL")
        self.scope = scope or [ "https://www.googleapis.com/auth/userinfo.email",
                                "https://www.googleapis.com/auth/userinfo.profile" ]

        self.session = OAuth2Session(
            self.client_id,
            scope=self.scope,
            redirect_uri=api.url_for(OAuthCallback, api_version="-", service="google", _external=True))

    def auth_redirect(self):
        return self.session.authorization_url(self.auth_url, prompt="select_account")[0]
