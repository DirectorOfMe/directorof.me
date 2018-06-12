import functools
from collections import OrderedDict

from . import client, schemas

class DOMEventRegistry:
    def __init__(self):
        self.registry = {}

    def listen(self, event_type):
        @functools.wraps(self.listen)
        def inner(handler):
            self.listen_for(event_type, handler)
            return handler

        return inner

    def listen_for(self, event_type, handler):
        self.registry.setdefault(event_type, OrderedDict())
        self.registry[event_type][id(handler)] = handler

    def stop(self, event_type, handler=None):
        if handler:
            handler = self.registry.get(event_type, {}).pop(id(handler), None)
            if not self.registry.get(event_type, True):
                del self.registry[event_type]
            return handler

        return self.registry.pop(event_type, None)

    def dispatch(self, event_data, installed_app=None):
        for handler in self.registry.get(event_data["event_type_slug"], {}).values():
            handler(event_data, installed_app=installed_app)

    def emit(self, client, event_type, data, event_time=None):
        ### TODO: Async
        try:
            event = { "event_type_slug": event_type, "data": data }
            event.update({k: event_time for k in ("event_time",) if event_time is not None})
            dumped = schemas.Event().dump(event)
            if dumped.errors:
                raise ValueError("\n".join(["{}: {}".format(k,v) for k,v in dumped.errors.items()]))

            client.post("event/events/", data=dumped.data)
        except Exception as e:
            # TODO: Logger
            import traceback; traceback.print_exc()
            print("Error processing event: {}".format(e))
