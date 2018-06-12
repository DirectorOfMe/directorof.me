import json
from furl import furl

from . import cipher, config as app_config
from directorofme.oauth import Slack

class Bot:
    slack_url = furl("https://slack.com/api/")

    def __init__(self, config, access_token, default_channel_id=None):
        self.default_channel_id = default_channel_id
        self.client = Slack(config, token={ "access_token": access_token })

        self.app_id = config["SLACK_APP_ID"]
        self.verification_token = config["SLACK_VERIFICATION_TOKEN"]

    def call(self, method, payload):
        url = self.slack_url.copy()
        url.path.add(method)
        resp = self.client.post(url.url, json=payload)

        # TODO -- handle errors
        try:
            data = resp.json()
            if not data["ok"]:
                raise Exception(data.get("error"))
            return data
        except json.JSONDecodeError:
            if resp.text.lower().strip() != "ok":
                raise Exception(resp.text)

    def whisper(self, message, user, channelish=None):
        print(1)
        body = { "channel": channelish or self.default_channel_id, "user": user }
        print(2)
        body.update(message)
        print(3)
        return self.call("chat.postEphemeral", body)

    def say(self, message, channelish=None):
        body = { "channel": channelish or self.default_channel_id }
        body.update(message)
        return self.call("chat.postMessage", body)

    def update(self, message, channelish=None):
        body = { "channel": channelish or self.default_channel_id }
        body.update(message)
        return self.call("chat.update", body)

    @classmethod
    def from_installed_app(cls, installed_app_data):
        integration = installed_app_data.get("config", {}).get("integrations", {}).get("slack")
        if integration is None:
            raise ValueError("No slack integration for app: {}".format(installed_app_data.get("id")))

        if integration.get("access_token") is None:
            raise ValueError("No slack access token for app: {}".format(installed_app_data.get("id")))

        return cls(
            app_config,
            cipher.decrypt(integration["access_token"]["value"]),
            default_channel_id=installed_app_data.get("config", {}).get("dm_channel_id")
        )
