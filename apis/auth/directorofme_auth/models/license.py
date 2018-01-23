'''
models/license.py -- License system

@author: Matt Story <matt@directorof.me>
'''
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from directorofme.orm import Model

from . import Group

__all__ = [ "License" ]

groups_to_license = Table(
    'group_to_license',
    Model.metadata,
    Column('license_id', UUIDType, ForeignKey('license.id')),
    Column('group_id', UUIDType, ForeignKey('group.id'))
)

profiles_to_license = Table(
    'profile_to_license',
    Model.metadata,
    Column('license_id', UUIDType, ForeignKey('license.id')),
    Column('profile_id', UUIDType, ForeignKey('profile.id'))
)

class License(Model):
    __tablename__ = "license"

    #: :class:`Group` objects to add to a session for an authenticated profile
    #: on this license.
    groups = relationship("Group", secondary=groups_to_license)

    #: id of :attr:`managing_group` for this :class:`License`
    managing_group_id = Column(UUIDType, ForeignKey(Group.id))
    #: :class:`Group` that can administer this license (e.g. add/remove profiles)
    #: this is different than having write permission to the license directly,
    #: which allows for adding groups and profiles without additional
    #: verification. A function that temporarily escalates permission can
    #: alter certain aspects of the license (like attaching and unaccting
    #: profiles) on behalf of members of this group.
    managing_group = relationship(Group)

    ### TODO: enforce quota
    #: max number of :attr:`.profiles` that can be associated with this license
    seats = Column(Integer, nullable=False)
    #: profiles attached to this license (up to :attr:`.seats`)
    profiles = relationship("Profile", secondary=profiles_to_license)
