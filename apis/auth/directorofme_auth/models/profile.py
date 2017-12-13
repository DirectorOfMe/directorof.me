'''
models/profile.py -- Profile system

@author: Matt Story <matt@directorof.me>
'''
from directorofme.stubtools import Model

__all__ = [ "Profile" ]

class Profile(Model):
    examples = {
        "matt": {
            "id": "matt",
            "email": "matt@directorof.me",
            "password": "sha512$100000$salt$0394a2ede332c9a13eb82e9b24631604c31df978b4e2f0fbd2c549944f9d79a5",

            "preferences": {
                "layout": "3-column",
                "beta_features": True,
                "main-dashboard": "dashboard/12345"
            }
        }
    }
