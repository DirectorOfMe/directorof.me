import pytest
from io import StringIO

from unittest import mock
from directorofme.events import DOMEventRegistry

class TestDOMEventRegistry:
    def test__basic(self):
        assert DOMEventRegistry().registry == {}, "new registry created successfully"

    def test__listen_and_listen_for(self):
        def handler(event_data, installed_app):
            pass

        dom_events = DOMEventRegistry()
        assert dom_events.registry == {}, "registry is empty"

        dom_events.listen_for("event-name", handler)
        assert list(dom_events.registry["event-name"].values()) == [handler], "handler registered"

        @dom_events.listen("event-name")
        def decorated_handler(event_data, installed_app):
            pass

        assert list(dom_events.registry["event-name"].values()) == [handler, decorated_handler], \
               "decorated_handler registered in order"

    def test__stop(self):
        dom_events = DOMEventRegistry()

        handler1, handler2 = object(), object()
        dom_events.registry = { "event-name": { id(handler1): handler1, id(handler2): handler2 } }

        dom_events.stop("event-name", handler1)
        assert dom_events.registry == { "event-name": { id(handler2): handler2 } }, "stop with handler works"

        dom_events.stop("event-name", handler2)
        assert dom_events.registry == {}, "stop removes empty lists"

        dom_events.registry = { "event-name": { id(handler1): handler1, id(handler2): handler2 } }
        dom_events.stop("event-name")
        assert dom_events.registry == {}, "stop with non-registered name works"

    def test__dispatch(self):
        dom_events = DOMEventRegistry()
        called = []

        @dom_events.listen("event-type")
        def handler(data, installed_app):
            assert data == { "event_type_slug": "event-type" }, "data correct"
            assert installed_app == "installed_app", "installed_app correct"
            called.append(True)

        dom_events.dispatch({ "event_type_slug": "event-type" }, "installed_app")
        assert called, "handler was called"

    def test__emit(self):
        client = mock.MagicMock()
        dom_events = DOMEventRegistry()

        dom_events.emit(client, "event-type", { "test": "data" })
        assert client.post.called_with("event/events/", data={
            "event_type_slug": "event-type",
            "data": { "test": "data" }
        }), "posted with correct data"

        with mock.patch("sys.stdout", StringIO()) as stdout:
            dom_events.emit(client, "event-type", {}, event_time="ABCEDAA")
            assert stdout.getvalue().find("Error") >= 0, "errors are logged"
