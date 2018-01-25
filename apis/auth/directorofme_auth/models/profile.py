'''
models/profile.py -- Profile system

@author: Matt Story <matt@directorof.me>
'''
from sqlalchemy import Column, String
from sqlalchemy_utils import JSONType, EmailType, UUIDType

from directorofme.orm import Model

__all__ = [ "Profile" ]

class Profile(Model):
    '''A profile, at the moement is what we authenticate against a third party
       service. It associates a user to a license and set of groups, which
       determines which applications, features and data a user has access to
       for a session. We may determine that one user may have multiple profiles
       in the future, but for now this should be assumed to be 1<>1 with a
       "person".
    '''
    __tablename__ = "profile"

    #: the name of the person using this profile
    name = Column(String(255), nullable=False)

    #: email as the unique identifier for our user, used by OAuth
    email = Column(EmailType, unique=True, nullable=False)

    #: preferences for this user (e.g. display color, layout, etc)
    preferences = Column(JSONType)
