import uuid
import copy
import flask
import functools
import base64
import json
import flask_jwt_extended as flask_jwt

from flask_restful import Resource, abort
from werkzeug.exceptions import Conflict
from oauthlib.oauth2 import OAuth2Error
from sqlalchemy.orm.attributes import flag_modified

from directorofme.oauth import Client, Slack
from directorofme.client import DOM
from directorofme.authorization import session, groups, requires, standard_permissions
from directorofme.flask.api import dump_with_schema, first_or_abort, uuid_or_abort, \
                                   load_query_params, abort_if_errors

from . import api, schemas
from .. import db, app as flask_app, config, spec, marshmallow
from ..models import Profile, InstalledApp, SlackBot, App, InstalledApp
from ..exceptions import EmailNotVerified

__all__ = [ "OAuth", "OAuthCallback", "Session", "with_service_client" ]


def _pack_state(dict_like):
    dumped = abort_if_errors(schemas.SessionQuerySchema().dumps(dict_like))
    return base64.b64encode(dumped.encode("utf-8")).decode("utf-8")

def _unpack_state(val):
    return {} if val is None else json.loads(base64.decodestring(val.encode("utf-8")).decode("utf-8"))

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

        try:
            kwargs.update(_unpack_state(kwargs.pop("state", None)).items())
        except Exception as e:
            abort(400, message="Invalid state passed")

        # stuff installed_app_id into state var if present
        state_args = ("installed_app_id", "invite")
        extra_args = {"state": _pack_state({k: kwargs.get(k) for k in state_args if kwargs.get(k) is not None})}

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
    def get(self, client, installed_app_id=None, invite=None):
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
            - in: query
              name: invite
              type: string
              format: uuid
              description: invitation token.
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
    ### TODO FACTOR
    @classmethod
    def emit_app_install_event(cls, session, installed_app):
        try:
            event_token = flask_jwt.create_access_token(session)
            csrf_token = flask_jwt.get_csrf_token(event_token)

            ### TODO: Async
            DOM(flask_app.config["SERVER_NAME"], access_token=event_token, access_csrf_token=csrf_token).post(
                "event/events/",
                data=schemas.PushEventToAppsSchema().dump({
                    "event_type_slug": "app-installed",
                    "event_time": installed_app.created,
                    "data": {
                        "installed_app_id": str(installed_app.id),
                        "app_slug": installed_app.app.slug
                }
            }).data)
        except Exception as e:
            # TODO: Logger
            import traceback; traceback.print_exc()
            print("Error processing event: {}".format(e))
        finally:
            return installed_app


    @requires.anybody
    @dump_with_schema(schemas.SessionSchema)
    @load_query_params(schemas.SessionQuerySchema)
    @with_service_client
    def get(self, client, installed_app_id=None, invite=None):
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
                schema: SessionSchema
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
            email, verified, name = client.confirm_identity(token)

            if not verified:
                raise EmailNotVerified(email)

            profile, slack_app, bot = None, None, None
            with session.do_as_root:
                ### SIGN-UP FLOW
                profile = Profile.query.filter(Profile.email == email).first()
                if profile is None and invite is not None:
                    first_or_abort(Profile.query.filter(Profile.id == invite), 409)
                    profile = Profile.create_profile(name=name, email=email)
                    db.session.add(profile)
                    db.session.flush()

                slack_app = first_or_abort(App.query.filter(App.slug == "slack"), 500)
                bot = self.bot_from_token(token, client, profile, slack_app.public_key)
                db.session.flush()
                if invite is not None and bot is None:
                    return flask.session, 302, {
                        "Location": Slack(
                            config,
                            callback_url=api.url_for(OAuthCallback, api_version="-", service="slack",
                                                     _external=True),
                            state=_pack_state({ "invite": invite }),
                            scopes=("bot", "commands", "dnd:read", "dnd:write", "chat:write:bot"),
                        ).authorization_url()
                    }

            if profile is None:
                abort(401, message="No profile for email: {}".format(email))

            # Now that we have our groups installed, we can query for the requested app
            new_session = _session_from_profile(profile, installed_app_id)

            flask.session.overwrite(new_session)
            flask.session.save = True

            status_code, location, new = 201, api.url_for(Session), False
            if invite and bot:
                # Redirect to slack bot
                installed_slack_app = InstalledApp.query.filter(InstalledApp.app == slack_app).first()
                if installed_slack_app is None:
                    with session.do_as_root:
                        new = True
                        installed_slack_app = slack_app.install_for_group(profile.group_of_one, config={
                            "integrations": {
                                "slack": {
                                    "access_token": {
                                        "encryption": "RSA",
                                        "value": bot.encrypted_access_token,
                                    }
                                }
                            }
                        })

                        db.session.add(installed_slack_app)
                        db.session.flush()

                        dom_token = flask_jwt.create_refresh_token(
                            _session_from_profile(profile, installed_slack_app.id))
                        csrf_token = flask_jwt.get_csrf_token(dom_token)

                        # re-grab a fresh object to manipulate
                        installed_slack_app.config["integrations"]["directorofme"] = {
                            "encryption": "RSA",
                            "value": slack_app.encrypt(json.dumps({
                                "refresh_token": dom_token,
                                "refresh_csrf_token": csrf_token
                            }))
                        }
                        flag_modified(installed_slack_app, "config")

                        db.session.add(installed_slack_app)
                        db.session.flush()

                status_code, location = 302, client.app_url()

            db.session.commit()
            ### XXX
            if new:
                self.emit_app_install_event(
                    _session_from_profile(profile, installed_slack_app.id),
                    installed_slack_app)
            return flask.session, status_code, { "Location": location }
        except OAuth2Error as e:
            return abort(400, message=str(e))
        except EmailNotVerified as e:
            return abort(400, message="Email ({}) not verified".format(str(e)))

    @classmethod
    def bot_from_token(cls, token, client, profile, public_key):
        """Get or create a bot from a slack token"""
        bot = None
        if client.name == "slack":
            team_id = token.get("team_id", token.get("team", {}).get("id"))
            bot = SlackBot.query.filter(SlackBot.team_id == team_id).first()
            if bot is None and token.get("bot") is not None:
                bot = SlackBot(
                    public_key=public_key,
                    access_token=token["bot"]["bot_access_token"],
                    installing_slack_user_id=token["user_id"],
                    installing_profile=profile,
                    team_id=token["team_id"],
                    bot_id=token["bot"]["bot_user_id"],
                    scopes = token["scope"][0].split(",")
                )
                db.session.add(bot)

        return bot


@spec.register_resource
@api.resource("/session", endpoint="session_api")
class Session(Resource):
    """
    Get or refresh a session.
    """
    @requires.user
    @dump_with_schema(schemas.SessionSchema)
    def get(self):
        """
        ---
        description: Fetch the session data associated with the current access token.
        parameters:
            - api_version
        responses:
            200:
                description: Decoded session data associate with the current access token.
                schema: SessionSchema
            403:
                description: No token for this session, or the token is not authenticated.
                schema: ErrorSchema
        """
        return flask.session

    @requires.anybody
    @flask_jwt.jwt_refresh_token_required
    @dump_with_schema(schemas.SessionSchema)
    def put(self):
        """
        ---
        description: Refresh a session using a refresh_token.
        parameters:
            - api_version
        responses:
            200:
                description: Decoded session data associate with the current access token.
                schema: SessionSchema
            401:
                description: No refresh token provided.
                schema: ErrorSchema
            409:
                description: Profile not found.
                schema: ErrorSchema
        """
        session_data = flask_jwt.get_jwt_identity() or {}
        if session_data:
            session_data = schemas.SessionSchema().load(session_data)
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
    @dump_with_schema(schemas.SessionSchema)
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
                schema: SessionSchema
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
                schema: SessionSchema
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


@spec.register_resource
@api.resource("/sign-up/<string:invite>", endpoint="sign_up_by_invite")
class SignUpByInvite(Resource):
    @load_query_params(schemas.SignUpQuerySchema)
    def get(self, invite):
        """
        ---
        description: Sign-up for DirectorOf.Me using an invitation token.
        parameters:
            - api_version
            - in: path
              name: invite
              type: string
              format: uuid
              description: invitation uuid.
        responses:
            302:
                description: Start the OAuth handshake with Slack to sign-up.
                headers:
                    Location:
                        description: Slack authorization url.
                        type: string
                        format: url
            400:
                description: Invalid invite format (must be a uuid).
                schema: ErrorSchema
            404:
                description: Invite not found.
                schema: ErrorSchema
        """
        with session.do_as_root:
            first_or_abort(Profile.query.filter(Profile.id == uuid_or_abort(invite)), 404)

        return None, 302, {
            "Location": Slack(
                config,
                callback_url=api.url_for(OAuthCallback, api_version="-", service="slack", _external=True),
                state=_pack_state({ "invite": invite })
            ).authorization_url()
        }
