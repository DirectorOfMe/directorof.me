from directorofme import DOMEventRegistry
from directorofme.client import DOM
from . import Bot, app, cipher

class DOMBotEventRegistry(DOMEventRegistry):
    def dispatch(self, event_data, installed_app=None):
        for handler in self.registry.get(event_data["event_type_slug"], {}).values():
            handler(Bot.from_installed_app(installed_app), event_data, installed_app=installed_app)

    def emit(self, installed_app, event_type, data, event_time=None):
        return super().emit(
            DOM.from_installed_app(app.config.get("SERVER_NAME"), cipher, installed_app),
            event_type,
            data,
            event_time=event_time
        )
