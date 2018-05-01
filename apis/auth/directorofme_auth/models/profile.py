'''
models/profile.py -- Profile system

@author: Matt Story <matt@directorof.me>
'''
# third party imports
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import JSONType, EmailType, UUIDType, generic_repr

# proprietary imports
from directorofme.authorization import groups
from directorofme.flask import Model

from . import GroupTypes, Group, License
from .license import profiles_to_license
from .exceptions import NoProfileError, MissingGroupError

__all__ = [ "Profile" ]

@generic_repr("email")
class Profile(Model):
    '''A profile, at the moement is what we authenticate against a third party
       service. It associates a user to a license and set of groups, which
       determines which applications, features and data a user has access to
       for a session. We may determine that one user may have multiple profiles
       in the future, but for now this should be assumed to be 1<>1 with a
       "person".
    '''
    __tablename__ = "profile"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is None:
            raise NoProfileError(
                "new profiles may only be created with Profile.create_profile"
            )

    #: the name of the person using this profile
    name = Column(String(255), nullable=False)

    #: email as the unique identifier for our user, used by OAuth
    email = Column(EmailType, unique=True, nullable=False)

    #: preferences for this user (e.g. display color, layout, etc)
    preferences = Column(JSONType)

    #: id of :attr:`parent` of this group
    group_of_one_id = Column(UUIDType, ForeignKey(Model.prefix_name("group.id")), nullable=False)

    #: all members of this :class:`.Group` are also members of parent.
    group_of_one = relationship("Group")

    # TODO: Quota enforcement
    #: all licenses associated with this profile, active or inactive
    licenses = relationship("License", secondary=profiles_to_license,
                            back_populates="profiles", lazy="dynamic")


    @classmethod
    def create_profile(cls, name, email, valid_through=None, preferences=None,
                       add_user_group=True, additional_groups=tuple(), **perms):
        '''Factory for generating a profile with all of the necessary related
           objects to make it useful. This is *the way* to create a new user.
        '''
        # setup the profile and force the id to be allocated
        profile = cls(id=cls.id.default.arg({}), name=name, email=email,
                      preferences=preferences, **perms)

        # create the group-of-one using the UUID as the display_name
        profile.group_of_one = Group(
            display_name=profile.id.hex,
            type=GroupTypes.data,
            **perms
        )

        profile.read += (profile.group_of_one.name,)
        perms["read"] = (profile.read,)
        profile.write += (profile.group_of_one.name,)

        profile_groups = [ profile.group_of_one ]
        if add_user_group:
            user_group = Group.query.filter(Group.name == groups.user.name).first()
            if user_group is None:
                raise MissingGroupError("user group is required but not found")
            profile_groups.append(user_group)

        # allocate a default license for this user (required for login)
        profile.licenses.append(License(
            valid_through = valid_through,
            groups = [g for g in profile_groups + list(additional_groups) if g is not None],
            managing_group = profile.group_of_one,
            seats = 1,
            **perms
        ))

        return profile
