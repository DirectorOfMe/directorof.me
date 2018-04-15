import flask
import functools
import flask_jwt_extended as flask_jwt

from flask_restful import Resource, abort
from oauthlib.oauth2 import OAuth2Error

from directorofme.authorization import session, groups
from directorofme_flask_restful import resource_url

from . import api
from ..oauth import Client
from ..models import Profile
from ..exceptions import EmailNotVerified, NoUserForEmail

__all__ = [ "OAuth", "OAuthCallback", "RefreshToken", "Session", "with_service_client" ]

supported_methods = ("login", "token")

### TODO: offline for integrations, but not for auth
def with_service_client(fn):
    @functools.wraps(fn)
    def inner(obj, service, method, *args, **kwargs):
        ClientForService = Client.client_by_name(service)
        if ClientForService is None:
            return abort(404, message="no oauth service named {}".format(service))

        if method not in supported_methods:
            return abort(404, message="{} is not a supported method. Only {} are "\
                                      "supported".format(service, supported_methods))

        callback_url = api.url_for(OAuthCallback, api_version="-", service=service, method=method, _external=True)
        print(callback_url)
        return fn(obj, ClientForService(callback_url, offline=(method == "token")), method, *args, **kwargs)

    return inner


@resource_url(api, "/oauth/<string:service>/<string:method>", endpoint="oauth_api")
class OAuth(Resource):
    @with_service_client
    def get(self, client, method):
        url = client.authorization_url()
        return { "auth_url": url }, 302, { "Location": url }


@resource_url(api, "/oauth/<string:service>/<string:method>/callback", endpoint="oauth_callback_api")
class OAuthCallback(Resource):
    @with_service_client
    def get(self, client, method):
        error = client.check_callback_request_for_errors(flask.request)
        if error:
            return abort(400, message=error)

        try:
            token = client.fetch_token(flask.request.url)
            email, verified = client.confirm_email(token)
            if not verified:
                raise EmailNotVerified(email)

            profile = Profile.query.filter(Profile.email == email).first()
            if not profile:
                raise NoUserForEmail(email)

            if method == "login":
                primary_groups = []
                for license in profile.licenses:
                    primary_groups += license.groups

                ### XXX: mix in app group
                flask.session.overwrite(session.Session(
                    save=True,
                    environment=profile.preferences or {},
                    app=None,
                    profile=session.SessionProfile.from_conforming_type(profile),
                    groups=[groups.Group.from_conforming_type(g) for group in primary_groups \
                                                                 for g in group.expand()]
                ))
                return flask.session

            return { "service": client.name, "token": token }

        except OAuth2Error as e:
            return abort(400, message=str(e))
        except EmailNotVerified as e:
            return abort(400, message="Email ({}) not verified".format(str(e)))
        except NoUserForEmail as e:
            return abort(404, message="No user associated with email ({})".format(email))


@resource_url(api, "/refresh", endpoint="refresh_jwt")
class RefreshToken(Resource):
    @flask_jwt.jwt_refresh_token_required
    def get(self):
        session_data = flask_jwt.get_jwt_identity() or {}
        session_data["save"] = True
        session_data["profile"] = session.SessionProfile(**session_data.get("profile", {}))
        session_data["groups"] = [groups.Group(**g) for g in session_data.get("groups", [])]
        flask.session.overwrite(session.Session(**session_data))
        return flask.session


@resource_url(api, "/session", endpoint="session_api")
class Session(Resource):
    def get(self):
        return flask.session
