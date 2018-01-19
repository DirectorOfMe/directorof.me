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

__all__ = [ "Group", "GroupTypes" ]

groups_to_profiles = Table(
    'group_to_profile',
    Model.metadata,
    Column('profile_id', UUIDType, ForeignKey('profile.id')),
    Column('group_id', UUIDType, ForeignKey('group.id'))
)


class GroupTypes(enum.Enum):
    '''GroupTypes defines the three types of group that are available. Groups
       determine access control by virue of being added to a groups list in
       the user's active session. The type of group determines which active
       authorization objects may add a particular group to a session.

       - A group with type :attr:`.app` would be added to a session by the
         active :attr:`InstalledApp.app` for this session.
       - A group with type :attr:`.license` would be added to a session by an
         active :class:`License` for this session.
       - A group with type :attr:`.profile` would be added to the session by
         a :class:`Profile` (essentially a user-defined group).
    '''
    app = 1
    license = 2
    profile = 3


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
