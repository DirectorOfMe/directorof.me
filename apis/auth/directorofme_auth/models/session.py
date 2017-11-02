import datetime

from . import Model, Query, Group

class Session(Model):
    query = Query({
        "123": {
            "session_id": "123",
            "expires": datetime.datetime.now(),
            "profile_id": "ms.director",
            "app_id": "directorof.me",
            "groups": [
                Group.query.get("app-auth"),
                Group.query.get("license-premium"),
                Group.query.get("profile-dom-staff"),
            ],
            "environment": {
                "layout": "two-column",
                "home-dashboard": "Ms. Director's Dashboard of Greatness"
            }
        }
    })
