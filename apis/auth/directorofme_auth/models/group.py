'''
models/group.py -- Group system

@author: Matt Story <matt@directorof.me>
'''
from sqlalchemy import Table, Column, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType, observes, generic_repr

from directorofme.orm import Model
from directorofme.authorization.groups import GroupTypes, Group as AuthGroup, Scope, scope

__all__ = [ "Group", "GroupTypes" ]

# through table for group -< profiles
groups_to_profiles = Table(
    'group_to_profile',
    Model.metadata,
    Column('profile_id', UUIDType, ForeignKey('profile.id')),
    Column('group_id', UUIDType, ForeignKey('group.id')))

@scope
@generic_repr("name")
class Group(Model):
    '''The basic building block of access control.'''
    __tablename__ = "group"
    __table_args__ = (
        UniqueConstraint("display_name", "type"),
        UniqueConstraint("scope", "scope_permission"),
    )

    #: re-declare id here for use in `remote_side` below
    id = Model.id

    #: unique name of this :class:`.Group`, derived from Type/Display-Name
    name = Column(String(34), unique=True, nullable=False)

    #: user-defined name of this :class:`.Group`
    display_name = Column(String(32), nullable=False)

    #: the group type determines which authorization objects are responsible
    #: for and authorized to add this group to a session.
    #: (see :class:`.GroupTypes` for more info)
    type = Column(Enum(GroupTypes), nullable=False)

    ###: TODO: enforce permissions check on this field ... there is a security
    ###: issue around being able to set this, as this group also gets pulled
    ###: into a session
    #: id of :attr:`parent` of this group
    parent_id = Column(UUIDType, ForeignKey("group.id"), nullable=True)

    #: all members of this :class:`.Group` are also members of parent.
    parent = relationship("Group", remote_side=[id])

    #: profiles referenced by this group
    profiles = relationship("Profile", secondary=groups_to_profiles)

    #: used by feature groups to identify a scope (realm) for discovery
    scope = Column(String(34), nullable=True)

    #: used by feature groups to identify the permission associated with this
    #: group/scope (realm) for discovery
    scope_permission = Column(String(20), nullable=True)

    @observes("display_name", "type")
    def slugify_name(self, *args, **kwargs):
        self.name = AuthGroup.from_conforming_type(self).name

    @classmethod
    def create_scope_groups(cls, scope):
        # type validation
        groups = []
        scope = Scope.from_conforming_type(scope)
        for perm_name, group in scope.perms.items():
            groups.append(cls(
                name=group.name,
                display_name=group.display_name,
                type=group.type,
                scope=scope.name,
                scope_permission=perm_name
            ))

        return groups

    @classmethod
    def create_group(cls, group):
        # type validation
        group = AuthGroup.from_conforming_type(group)
        return cls(name=group.name, display_name=group.display_name, type=group.type)
