from furl import furl
from directorofme.client import DOM
from . import dom_events, cipher, app

@dom_events.listen("app-installed")
class AppInstallHandler:
    def __init__(self, bot, event_data, installed_app):
        self.bot = bot
        self.event_data = event_data
        self.installed_app = installed_app

        try:
            method = getattr(self, event_data.get("data", {}).get("app_slug"))
        except AttributeError:
            pass
        else:
            return method()

    @property
    def client(self):
        return DOM.from_installed_app(app.config["SERVER_NAME"], cipher, self.installed_app)

    def welcome_message(self, skip_calendar=False, skip_jira=False, **message):
        actions = []
        if not skip_calendar:
            actions.append({
                "text": "Google Calendar",
                "type": "button",
                "url": furl("https://demo.directorof.me/api/-/calendar/install").add(message).url,
            })

        if not skip_jira:
            actions.append({
                "name": "integration",
                "text": "Jira",
                "value": "jira",
                "type": "button"
            })

        message.update({
            "attachments": [
                {
                    "color": "#1AA79D",
                    "title": "Let's get started!",
                    "text": "DirectorOf.Me helps you have your best day every day."\
                            " To do this we work with your existing tools to help provide"\
                            " you with the insights you need to improve your habits.",

                    "callback_id": "integrate",
                    "actions": actions,
                }
            ]
        })
        return message


    def slack(self):
        # TODO: save in an event so we can update here
        result = self.bot.say(self.welcome_message())
        with_ts = self.welcome_message(ts=result["ts"])
        with_ts["channel"] = result["channel"]
        self.bot.update(with_ts)
        dom_events.emit(self.installed_app, "slack-message-sent", result)


    # TODO: actually do what we want to do here
    def calendar(self):
        calendar_app = self.client.get("auth/installed_apps/{}".format(
            str(self.event_data["data"]["installed_app_id"])
        ))
        self.bot.update(self.welcome_message(
            ts=calendar_app["config"].get("installed_from_message"),
            skip_calendar=True
        ))
        self.bot.whisper({
            "text": ":white_check_mark: You installed Google Calendar"
        }, self.installed_app["config"]["user_id"])

    def project_management(self):
        self.bot.say({ "text": "You just installed the project management app" })


@dom_events.listen("daily-rhythm")
def daily_rhythm(bot, event_data, installed_app):
    pass
