'''
models/license.py -- License system

@author: Matt Story <matt@directorof.me>
'''
from directorofme.stubtools import Model

from . import Profile, Group

class License(Model):
    examples = {
        "12345": {
            "groups": [
                Group.query.get("license/premium")
            ],
            "managing_group": Group.query.get("group/dom-admin"),
            "seats": 1,
            "profiles": [
                Profile.query.get("matt")
            ],
        }
    }
