'''
models/license.py -- License system

@author: Matt Story <matt@directorof.me>
'''
from directorofme.stubtools import Model

from . import Profile, Group

__all__ = [ "License" ]

class License(Model):
    examples = {
        "12345": {
            "groups": [
                Group.query.get("license/premium")
            ],
            "managing_group": Group.query.get("profile/dom-admin"),
            "seats": 1,
            "profiles": [
                Profile.query.get("matt")
            ],
        }
    }
