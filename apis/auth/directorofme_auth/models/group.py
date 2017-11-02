'''
models/group.py -- Group system

@author: Matt Story <matt@directorof.me>
'''

from directorofme.stubtools import Model

class Group(Model):
    examples = {
        "app/auth": {
            "type": "app",
            "name": "auth",
            "id": "app/auth",
            "parent": None
        },
        "app/dashboard": {
            "type": "app",
            "id": "app-dashboard",
            "name": "dashboard",
            "parent": "app/auth",
        },
        "license/free": {
            "type": "license",
            "id": "license/free",
            "name": "free",
            "parent": None,
        },
        "license/premium": {
            "type": "license",
            "id": "license/premium",
            "name": "premium",
            "parent": "license/free",
        },
        "group/dom-staff": {
            "type": "group",
            "id": "group/dom-staff",
            "name": "dom-staff",
            "parent": None,
            "users": []
        },
        "group/dom-admin": {
            "type": "group",
            "id": "group/dom-admin",
            "name": "dom-admin",
            "parent": "dom-staff",
            "users": [
                User.query.get("matt")
            ]
        }
    }
