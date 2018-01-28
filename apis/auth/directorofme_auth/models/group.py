'''
models/group.py -- Group system

@author: Matt Story <matt@directorof.me>
'''
import enum

from sqlalchemy import Table, Column, String, Enum, ForeignKey, \
                       UniqueConstraint, CheckConstraint
from sqlalchemy.types import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType, observes
from slugify import slugify

from directorofme.orm import Model
from directorofme.authorization.groups import GroupTypes

__all__ = [ "Group" ]

groups_to_profiles = Table(
    'group_to_profile',
    Model.metadata,
    Column('profile_id', UUIDType, ForeignKey('profile.id')),
    Column('group_id', UUIDType, ForeignKey('group.id')))

class Group(Model):
    '''The basic building block of access control.'''
    __tablename__ = "group"
    __table_args__ = (
        UniqueConstraint("display_name", "group_type"),
    )

    #: unique name of this :class:`.Group`, derived from Type/Display-Name
    name = Column(String(20), unique=True, nullable=False)

    #: user-defined name of this :class:`.Group`
    display_name = Column(String(18), nullable=False)

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

    @observes("display_name", "group_type")
    def slugify_name(self, display_name, group_type):
        if self.name is None and display_name is not None and group_type is not None:
                self.name = slugify("{}-{}".format(group_type.value, display_name))
