import datetime

from . import Model, Query

class Session(Model):
    query = Query({
        "123": {
            "session_id": "123",
            "expires": datetime.datetime.now(),
            "profile_id": "ms.director",
            "app_id": "directorof.me",
            "groups": [
                { "group_type": "app", "group_id": "core" },
                { "group_type": "license", "group_id": "premium" },
                { "group_type": "profile", "group_id": "dom-staff" },
            ],
            "environment": {
                "layout": "two-column",
                "home-dashboard": "Ms. Director's Dashboard of Greatness"
            }
        }
    })
