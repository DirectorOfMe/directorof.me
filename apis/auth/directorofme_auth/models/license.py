'''
models/license.py -- License system

@author: Matt Story <matt@directorof.me>
'''
from sqlalchemy import Table, Column, Integer, DateTime, Text, ForeignKey, Sequence
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from directorofme.authorization.orm import Model

from . import Group

__all__ = [ "License" ]

groups_to_license = Table(
    Model.prefix_name('group_to_license'),
    Model.metadata,
    Column('license_id', UUIDType, ForeignKey(Model.prefix_name('license.id')), nullable=False),
    Column('group_id', UUIDType, ForeignKey(Model.prefix_name('group.id')), nullable=False))

profiles_to_license = Table(
    Model.prefix_name('profile_to_license'),
    Model.metadata,
    Column('license_id', UUIDType, ForeignKey(Model.prefix_name('license.id')), nullable=False),
    Column('profile_id', UUIDType, ForeignKey(Model.prefix_name('profile.id')), nullable=False),
    Column('created', Integer, Sequence("profiles_to_license_seq"), nullable=False))

class License(Model):
    __tablename__ = "license"

    #: :class:`Group` objects to add to a session for an authenticated profile
    #: on this license.
    groups = relationship("Group", secondary=groups_to_license, backref="licenses")

    #: id of :attr:`managing_group` for this :class:`License`
    managing_group_id = Column(UUIDType, ForeignKey(Group.id), nullable=False)

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
    profiles = relationship("Profile", secondary=profiles_to_license,
                            back_populates="licenses", lazy="dynamic",
                            order_by=profiles_to_license.c.created)

    # TODO: reconsider this default
    #: this profile is valid through (null is good forever)
    valid_through = Column(DateTime, nullable=True, default=None)

    #: any pertinent notes on this license.
    notes = Column(Text, nullable=False, default="")

    @property
    def active_profiles(self):
        if self.seats >= 0:
            return self.profiles.limit(self.seats)
        return self.profiles
