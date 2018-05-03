import uuid
import flask
import functools
import flask_jwt_extended as flask_jwt

from flask_restful import Resource, abort, reqparse
from oauthlib.oauth2 import OAuth2Error

from directorofme.authorization import session, groups, requires, standard_permissions

from . import api
from .. import Model
from ..oauth import Client
from ..models import Profile, InstalledApp
from ..exceptions import EmailNotVerified, NoUserForEmail

__all__ = [ "OAuth", "OAuthCallback", "RefreshToken", "Session", "with_service_client" ]

supported_methods = ("login", "token")

def _parse_session_args():
    parser = reqparse.RequestParser()
    parser.add_argument('installed_app_id', type=uuid.UUID, help='UUID of the Installed App this session is for')
    return parser.parse_args()


def _session_from_profile(profile, installed_app_id):
    groups_list = []
    with session.do_as_root:
        groups_list = [ groups.Group.from_conforming_type(group) for license in profile.licenses \
                                                                 for license_group in license.groups \
                                                                 for group in license_group.expand() ]

    with session.do_with_groups(*(groups_list + [Model.__scope__.read] if Model.__scope__ else [])):
        new_session = session.Session.empty()
        new_session.environment = profile.preferences or {}
        new_session.profile = session.SessionProfile.from_conforming_type(profile)
        new_session.groups += groups_list
        new_session.default_object_perms = {
            name: [profile.group_of_one.name] for name in standard_permissions
        }

        if installed_app_id is not None:
            installed_app = InstalledApp.query.filter(InstalledApp.id == installed_app_id).first()
            if installed_app is None:
                abort(404, message="No app found for {}".format(installed_app_id))

            new_session.app = session.SessionApp.from_conforming_type(installed_app)
            with session.do_as_root:
                new_session.groups += [
                    groups.Group.from_conforming_type(group) for access_group in installed_app.access_groups \
                                                             for group in access_group.expand()
                ]

    return new_session


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
        extra_args = {k: v for k, v in _parse_session_args().items() if k == "installed_app_id"}
        callback_url = api.url_for(OAuthCallback, api_version="-", service=service, method=method,
                                   _external=True, **extra_args)
        return fn(obj, ClientForService(callback_url, offline=(method == "token")), method, *args, **kwargs)

    return inner


@api.resource("/oauth/<string:service>/<string:method>", endpoint="oauth_api")
class OAuth(Resource):
    @requires.anybody
    @with_service_client
    def get(self, client, method):
        url = client.authorization_url()
        return { "auth_url": url }, 302, { "Location": url }


@api.resource("/oauth/<string:service>/<string:method>/callback", endpoint="oauth_callback_api")
class OAuthCallback(Resource):
    @requires.anybody
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

            profile = None
            with session.do_as_root:
                profile = Profile.query.filter(Profile.email == email).first()

            if not profile:
                raise NoUserForEmail(email)

            if method == "login":
                # Now that we have our groups installed, we can query for the requested app
                new_session = _session_from_profile(profile, _parse_session_args().get("installed_app_id"))
                print(new_session)
                flask.session.overwrite(new_session)
                flask.session.save = True
                return flask.session

            return { "service": client.name, "token": token }

        except OAuth2Error as e:
            return abort(400, message=str(e))
        except EmailNotVerified as e:
            return abort(400, message="Email ({}) not verified".format(str(e)))
        except NoUserForEmail as e:
            return abort(404, message="No user associated with email ({})".format(email))


@api.resource("/refresh", endpoint="refresh_jwt")
class RefreshToken(Resource):
    @requires.anybody
    @flask_jwt.jwt_refresh_token_required
    def get(self):
        session_data = flask_jwt.get_jwt_identity() or {}
        app_data = session_data.get("app", {})

        session_data["save"] = True
        session_data["profile"] = session.SessionProfile(**session_data.get("profile", {}))
        session_data["app"] = session.SessionApp(**app_data) if app_data else None
        session_data["groups"] = [groups.Group(**g) for g in session_data.get("groups", [])]
        flask.session.overwrite(session.Session(**session_data))
        return flask.session


@api.resource("/session", endpoint="session_api")
class Session(Resource):
    @requires.user
    def get(self):
        return flask.session

@api.resource("/session/<installed_app_id>", endpoint="session_for_app_api")
class SessionForApp(Resource):
    @requires.user
    def get(self, installed_app_id):
        profile = Profile.query.filter(Profile.id == flask.session.profile.id).first()
        new_session = _session_from_profile(profile, installed_app_id)

        flask.session.overwrite(new_session)
        flask.session.save = True
        return flask.session
