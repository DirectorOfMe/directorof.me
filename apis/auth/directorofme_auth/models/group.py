from . import Model, Query

class Group(Model):
    query = Query({
        "app-auth": {
            "type": "app",
            "name": "auth",
            "id": "app-auth",
            "parent": None
        },
        "app-dashboard": {
            "type": "app",
            "id": "app-dashboard",
            "name": "dashboard",
            "parent": "app-auth",
        },
        "license-free": {
            "type": "license",
            "id": "license-free",
            "name": "free",
            "parent": None,
        },
        "license-premium": {
            "type": "license",
            "id": "license-premium",
            "name": "premium",
            "parent": "license-free",
        },
        "profile-dom-staff": {
            #TODO: this doesn't feel great.
            "type": "profile",
            "id": "profile-dom-staff",
            "name": "dom-staff",
            "parent": None,
            #TODO: Users?
        }
    })
