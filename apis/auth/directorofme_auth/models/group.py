'''
models/group.py -- Group system

@author: Matt Story <matt@directorof.me>
'''
import enum

from sqlalchemy import Table, Column, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType, observes
from slugify import slugify

from directorofme.orm import Model
from directorofme.authorization import GroupTypes

__all__ = [ "Group" ]

groups_to_profiles = Table(
    'group_to_profile',
    Model.metadata,
    Column('profile_id', UUIDType, ForeignKey('profile.id')),
    Column('group_id', UUIDType, ForeignKey('group.id')))

class Group(Model):
    '''The basic building block of access control.'''
    __tablename__ = "group"

    #: unique, user-defined name of this :class:`.Group`
    name = Column(String(20), unique=True, nullable=False)

    #: unique, url-safe name used to fetch :class:`.Group` objects from the API
    slug = Column(String(20), index=True, unique=True, nullable=False)

    #: the group type determines which authorization objects are responsible
    #: for and authorized to add this group to a session.
    #: (see :class:`.GroupTypes` for more info)
    group_type = Column(Enum(GroupTypes), nullable=False)

    #: id of :attr:`parent` of this group
    parent_id = Column(UUIDType, ForeignKey("group.id"), nullable=True)

    #: all members of this :class:`.Group` are also members of parent.
    parent = relationship("Group")

    #: profiles referenced by this group
    profiles = relationship("Profile", secondary=groups_to_profiles)

    ### TODO: factor this -- also used in models/app.py
    @observes("name")
    def slugify_name(self, name):
        self.slug = slugify(name)
