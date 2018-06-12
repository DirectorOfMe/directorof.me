import flask

from flask_restful import abort

from directorofme.authorization import requires
from directorofme.flask.api import load_with_schema, abort_if_errors, Resource
from directorofme.schemas import Event, InstalledApp

from . import api, config, spec, marshmallow, dom_events

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


### TODO: Nested structures, and verify
@spec.register_schema("SlackInteractionSchema")
class SlackInteractionSchema(marshmallow.Schema):
    token = marshmallow.String(required=True)
    type = marshmallow.String(required=True)

    actions = marshmallow.List(marshmallow.Dict)
    callback_id = marshmallow.String(required=True)

    channel = marshmallow.Dict()
    team = marshmallow.Dict()
    user = marshmallow.Dict()

    action_ts = marshmallow.Float()
    message_ts = marshmallow.Float()

    attachment_id = marshmallow.String()
    is_app_unfurl = marshmallow.Boolean()
    original_message = marshmallow.Dict()

    response_url = marshmallow.Url()
    trigger_id = marshmallow.String()


@spec.register_resource
@api.resource("/interaction", endpoint="interaction_api")
class SlackInteraction(Resource):
    def post(self):
        payload = abort_if_errors(SlackInteractionSchema().loads(flask.request.values.get("payload", {})))
        if payload["token"] != config["SLACK_VERIFICATION_TOKEN"]:
            abort(403, message="interaction endpoint may only be used by slack")

        print(payload)
        return payload["original_message"]
