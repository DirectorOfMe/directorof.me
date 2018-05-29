import uuid
import flask
import functools
import flask_jwt_extended as flask_jwt

from flask_restful import Resource, abort
from werkzeug.exceptions import Conflict
from oauthlib.oauth2 import OAuth2Error

from directorofme.oauth import Client
from directorofme.authorization import session, groups, requires, standard_permissions
from directorofme.flask.api import dump_with_schema, first_or_abort, uuid_or_abort, load_query_params

from . import api, schemas
from .. import db, config, spec, marshmallow
from ..models import Profile, InstalledApp
from ..exceptions import EmailNotVerified

__all__ = [ "OAuth", "OAuthCallback", "Session", "with_service_client" ]


def _session_from_profile(profile, installed_app_id):
    # we must always grant read access to auth data strucuture scope or the user can't do anything
    groups_list = [db.Model.__scope__.read] if db.Model.__scope__ else []
    with session.do_as_root:
        groups_list += [ groups.Group.from_conforming_type(group) for license in profile.licenses \
                                                                  for license_group in license.groups \
                                                                  for group in license_group.expand() ]

    with session.do_with_groups(*groups_list):
        new_session = session.Session.empty()
        new_session.environment = profile.preferences or {}
        new_session.profile = session.SessionProfile.from_conforming_type(profile)
        new_session.groups += groups_list
        new_session.default_object_perms = {
            name: [profile.group_of_one.name] for name in standard_permissions
        }

        if installed_app_id is not None:
            installed_app = first_or_abort(InstalledApp.query.filter(InstalledApp.id == installed_app_id), 409)

            new_session.app = session.SessionApp.from_conforming_type(installed_app)
            with session.do_as_root:
                new_session.groups += [
                    groups.Group.from_conforming_type(group) for access_group in installed_app.access_groups \
                                                             for group in access_group.expand()
                ]

    return new_session


def with_service_client(fn):
    @functools.wraps(fn)
    def inner(obj, service, *args, **kwargs):
        ClientForService = Client.by_name(service)
        if ClientForService is None:
            return abort(404, message="no oauth service named {}".format(service))

        # stuff installed_app_id into state var if present
        extra_args = {"state": kwargs.get(k) for k in ("installed_app_id", ) if kwargs.get(k)}
        kwargs.update({"installed_app_id": kwargs.pop("state", None) for k in ("state",) if kwargs.get(k)})

        callback_url = api.url_for(OAuthCallback, api_version="-", service=service, _external=True)
        return fn(obj, ClientForService(config, callback_url=callback_url, **extra_args), *args, **kwargs)

    return inner

@spec.register_resource
@api.resource("/oauth/<string:service>", endpoint="oauth_api")
class OAuth(Resource):
    """
    An endpoint for authenticating with OAuth and a 3rd party.
    """
    @requires.anybody
    @load_query_params(schemas.SessionQuerySchema)
    @with_service_client
    def get(self, client, installed_app_id=None):
        """
        ---
        description: Start the OAuth authentication process.
        parameters:
            - api_version
            - service
            - in: query
              name: installed_app_id
              type: string
              format: uuid
              description: optional id for application that should be loaded for this session.
        responses:
            302:
                description: Redirect to 3rd party authorization url.
            404:
                description: No service registered with the provided name.
                schema: ErrorSchema
        """
        url = client.authorization_url()
        return { "auth_url": url }, 302, { "Location": url }


###: TODO: re-implement to Oauth2 token / refresh endpoint specs
@spec.register_resource
@api.resource("/oauth/<string:service>/callback", endpoint="oauth_callback_api")
class OAuthCallback(Resource):
    """
    Callback used by third parties after successful authentication.
    """
    @requires.anybody
    @dump_with_schema(schemas.SessionResponseSchema)
    @load_query_params(schemas.SessionQuerySchema)
    @with_service_client
    def get(self, client, installed_app_id=None):
        """
        ---
        description: Callback from 3rd party OAuth Url.
        parameters:
            - api_version
            - service
            - in: query
              name: installed_app_id
              type: string
              format: uuid
              description: optional id for application that should be loaded for this session.
        responses:
            201:
                description: New session successfully created.
                schema: SessionResponseSchema
                headers:
                    Location:
                        description: URL for the newly created session.
                        type: string
                        format: url
            400:
                description: Error forwarded from 3rd party, or email has not
                             been verified by 3rd party.
                schema: ErrorSchema
            401:
                description: No user found for email provided by third party.
                schema: ErrorSchema
            404:
                description: No service registered with the provided name.
                schema: ErrorSchema
            409:
                description: No app found with the provided name.
                schema: ErrorSchema
        """
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
                profile = first_or_abort(Profile.query.filter(Profile.email == email), 401)

            # Now that we have our groups installed, we can query for the requested app
            new_session = _session_from_profile(profile, installed_app_id)
            flask.session.overwrite(new_session)
            flask.session.save = True
            return flask.session, 201, { "Location": api.url_for(Session) }

        except OAuth2Error as e:
            return abort(400, message=str(e))
        except EmailNotVerified as e:
            return abort(400, message="Email ({}) not verified".format(str(e)))


@spec.register_resource
@api.resource("/session", endpoint="session_api")
class Session(Resource):
    """
    Get or refresh a session.
    """
    @requires.user
    @dump_with_schema(schemas.SessionResponseSchema)
    def get(self):
        """
        ---
        description: Fetch the session data associated with the current access token.
        parameters:
            - api_version
        responses:
            200:
                description: Decoded session data associate with the current access token.
                schema: SessionResponseSchema
            403:
                description: No token for this session, or the token is not authenticated.
                schema: ErrorSchema
        """
        return flask.session

    @requires.anybody
    @flask_jwt.jwt_refresh_token_required
    @dump_with_schema(schemas.SessionResponseSchema)
    def put(self):
        """
        ---
        description: Refresh a session using a refresh_token.
        parameters:
            - api_version
        responses:
            200:
                description: Decoded session data associate with the current access token.
                schema: SessionResponseSchema
            401:
                description: No refresh token provided.
                schema: ErrorSchema
            404:
                description: Profile not found.
                schema: ErrorSchema
        """
        session_data = flask_jwt.get_jwt_identity() or {}
        if session_data:
            session_data = schemas.SessionResponseSchema().load(session_data)
            if session_data.errors:
                messages = ["{}: {}".format(k,v) for k,v in session_data.errors.items()]
                abort(400, message="Validation failed: {}".format(", ".join(messages)))

            session_data = session_data.data

        app_data = session_data.get("app", {})

        session_data["save"] = True
        session_data["profile"] = session.SessionProfile(**session_data.get("profile", {}))
        session_data["app"] = session.SessionApp(**app_data) if app_data else None
        session_data["groups"] = [groups.Group(**g) for g in session_data.get("groups", [])]
        flask.session.overwrite(session.Session(**session_data))
        return flask.session

@spec.register_resource
@api.resource("/session/<installed_app_id>", endpoint="session_for_app_api")
class SessionForApp(Resource):
    """
    Create a new token for a particular application that the current token has access to.
    """
    @requires.user
    @dump_with_schema(schemas.SessionResponseSchema)
    def post(self, installed_app_id):
        """
        ---
        description: Create a new token for a particular application.
        parameters:
            - api_version
            - in: path
              name: installed_app_id
              type: string
              format: uuid
              description: uuid of the installed app to create a token for.
        responses:
            201:
                description: New session successfully created.
                schema: SessionResponseSchema
                headers:
                    Location:
                        description: URL for the newly created session.
                        type: string
                        format: url
            400:
                description: Invalid uuid.
                schema: ErrorSchema
            401:
                description: No profile associated with session.
                schema: ErrorSchema
            403:
                description: Insufficient permissions to create new session.
                schema: ErrorSchema
            404:
                description: No app found with the provided ID.
                schema: ErrorSchema
        """
        profile = first_or_abort(Profile.query.filter(Profile.id == flask.session.profile.id), 401)
        try:
            new_session = _session_from_profile(profile, uuid_or_abort(str(installed_app_id)))
        except Conflict:
            abort(404, message="No app for id {}".format(str(installed_app_id)))

        flask.session.overwrite(new_session)
        flask.session.save = True
        return flask.session, 201, { "Location": api.url_for(Session) }


@spec.register_resource
@api.resource("/sudo/<string:email>", endpoint="sudo_api")
class Sudo(Resource):
    @requires.admin
    @load_query_params(schemas.SessionQuerySchema)
    def post(self, email, installed_app_id=None):
        """
        ---
        description: Create a token for a different user (admin only).
        parameters:
            - api_version
            - email
            - in: path
              name: installed_app_id
              type: string
              format: uuid
              description: uuid of the installed app to create a token for.
        responses:
            201:
                description: New session successfully created.
                schema: SessionResponseSchema
                headers:
                    Location:
                        description: URL for the newly created session.
                        type: string
                        format: url
            400:
                description: Invalid uuid.
                schema: ErrorSchema
            403:
                description: Not an admin.
                schema: ErrorSchema
            404:
                description: No profile found with the provided email.
                schema: ErrorSchema
            409:
                description: No app found with the provided id.
                schema: ErrorSchema
        """
        with session.do_as_root:
            profile = first_or_abort(Profile.query.filter(Profile.email == email))

        new_session = _session_from_profile(profile, installed_app_id)
        flask.session.overwrite(new_session)
        flask.session.save = True
        return flask.session, 201, { "Location": api.url_for(Session) }
