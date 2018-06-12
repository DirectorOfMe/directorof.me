from . import dom_events

@dom_events.listen("start-of-day")
def daily_summary(event_data, installed_app):
    print(event_data, installed_app)
    pass
