import flask

from furl import furl
from flask_restful import abort

from directorofme.oauth import Google, Slack
from directorofme.client import DOM
from directorofme.authorization import requires
from directorofme.flask.api import load_with_schema, load_query_params, abort_if_errors, Resource
from directorofme.schemas import Event, InstalledApp

from . import api, app, config, spec, marshmallow, dom_events

@spec.register_resource
@api.resource("/handle-event", endpoint="handle_event_api")
class HandleDOMEvent(Resource):
    @spec.register_schema("PushedEventSchema")
    class PushedEvent(marshmallow.Schema):
        event = marshmallow.Nested(Event)
        installed_app = marshmallow.Nested(InstalledApp)

    @requires.push
    @load_with_schema(PushedEvent)
    def post(self, event_and_installed_app):
        dom_events.dispatch(event_and_installed_app["event"], event_and_installed_app["installed_app"])
        return None, 204


def google(state=None):
    return Google(
        config,
        callback_url=api.url_for(OAuthCallback, api_version="-", service="google", _external=True),
        scopes=("https://www.googleapis.com/auth/calendar",),
        offline=True,
        state=state
    )

@spec.register_resource
@api.resource("/install", endpoint="install")
class Install(Resource):
    @spec.register_schema("InstallQuerySchema")
    class InstallQuerySchema(marshmallow.Schema):
        ts = marshmallow.String()

    @load_query_params(InstallQuerySchema)
    def get(self, ts=None):
        apps = DOM.from_request(flask.request, app).get("auth/installed_apps/", params={ "app": "calendar" })
        if apps.get("collection"):
            return apps.get("collection")[0], 302, { "Location": Slack(config).app_url() }

        return None, 302, { "Location": google(state=ts).authorization_url() }


@spec.register_resource
@api.resource("/install/<string:service>/callback", endpoint="install_callback")
class OAuthCallback(Resource):
    @spec.register_schema("OAuthCallbackQuerySchema")
    class OAuthCallbackQuerySchema(marshmallow.Schema):
        state = marshmallow.String()

    @load_query_params(OAuthCallbackQuerySchema)
    def get(self, service, state=None):
        if service != "google":
            abort(400, message="Only google calendar currently supported")

        oauth_client = google(state=state)
        error = oauth_client.check_callback_request_for_errors(flask.request)
        if error:
            return abort(400, message=error)

        refresh_token = oauth_client.fetch_token(flask.request.url)["refresh_token"]
        client = DOM.from_request(flask.request, app)

        cal_app = client.get("auth/apps/calendar")
        installed = client.post("auth/apps/calendar/install/", data={
            "scopes": cal_app["requested_scopes"],
            "config": {
                "installed_from_message": state,
                "scopes": ["https://www.googleapis.com/auth/calendar",],
                "integrations": {
                    "google": {
                        "refresh_token": {
                            "encryption": "RSA",
                            "value": client.post("auth/apps/calendar/encrypt/", data={
                                "encryption": "RSA",
                                "value": refresh_token
                            })["value"]
                        }
                    }
                }
            }
        })

        return installed, 302, { "Location": Slack(config).app_url() }
