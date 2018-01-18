'''
models/session.py -- Session system

@author: Matt Story <matt@directorof.me>
'''
# WILL BE FRONT-END
'''
class Session(Model):
    examples = {
        "123": {
            "id": "123",
            "expires": datetime.datetime.now(),
            "profile": Profile.query.get("matt"),
            "license": License.query.get("12345"),
            "installed_app": InstalledApp.query.get("dashboard/install/12345"),
            "groups": [
                Group.query.get("app/auth"),
                Group.query.get("license/premium"),
                Group.query.get("profile/dom-staff"),
            ],
            "environment": {
                "layout": "two-column",
                "home-dashboard": "Ms. Director's Dashboard of Greatness"
            }
        }
    }
'''
