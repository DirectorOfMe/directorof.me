'''
models/group.py -- Group system

@author: Matt Story <matt@directorof.me>
'''
from sqlalchemy import Table, Column, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.sql.expression import literal
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.event import listen
from sqlalchemy_utils import UUIDType, generic_repr

from directorofme.orm import Model
from directorofme.authorization.groups import GroupTypes, Group as AuthGroup, Scope, scope

from .. import db

__all__ = [ "Group", "GroupTypes" ]

# through table for group -< groups
group_to_group = Table(
    'group_to_group',
    Model.metadata,
    Column('parent_group_id', UUIDType, ForeignKey('group.id')),
    Column('member_group_id', UUIDType, ForeignKey('group.id')))

@scope
@generic_repr("name")
class Group(Model):
    '''The basic building block of access control.'''
    __tablename__ = "group"
    __table_args__ = (
        UniqueConstraint("display_name", "type"),
        UniqueConstraint("scope", "scope_permission"),
    )
    #: unique name of this :class:`.Group`, derived from Type/Display-Name
    name = Column(String(34), unique=True, nullable=False)

    #: user-defined name of this :class:`.Group`
    display_name = Column(String(32), nullable=False)

    #: the group type determines which authorization objects are responsible
    #: for and authorized to add this group to a session.
    #: (see :class:`.GroupTypes` for more info)
    type = Column(Enum(GroupTypes), nullable=False)

    members = relationship(
        "Group",
        secondary=group_to_group,
        primaryjoin="Group.id == group_to_group.c.parent_group_id",
        secondaryjoin="Group.id == group_to_group.c.member_group_id",
        backref="member_of"
    )

    #: used by feature groups to identify a scope (realm) for discovery
    scope = Column(String(34), nullable=True)

    #: used by feature groups to identify the permission associated with this
    #: group/scope (realm) for discovery
    scope_permission = Column(String(20), nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slugify_name()

    def slugify_name(self, **kwargs):
        try:
            self.name = AuthGroup(**{
                "name": self.name,
                "display_name": kwargs.get("display_name", self.display_name),
                "type": kwargs.get("type", self.type),
            }).name
        except ValueError:
            pass

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

    def expand(self):
        '''
        THIS NEEDS A GOOD DOC STRING
        '''
        g2g = aliased(group_to_group, name="g2g")
        members = db.session.query(
                # in order to make sure self is part of the set
                # we start by selecting our own id from group,
                # before recursing to group_to_group
                Group.id.label("parent_group_id"),
                # to preent infinite recursion, we track seen ids in an array
                array([Group.id]).label("path"),
            ).filter(
                # just this group
                Group.id == self.id
            # make a common table expression (WITH members(...) AS ())
            ).cte(name="members", recursive=True)

        # recursive query to walk up the groups tree
        members = members.union_all(
            db.session.query(
                # get the parent id from the group mapping table (next node up)
                g2g.c.parent_group_id.label("parent_group_id"),
                # add it to the array of seen ids
                (members.c.path + array([g2g.c.parent_group_id])).label("path"),
            # force selection from the CTE synthetic table first
            ).select_from(members).join(
                # join to the group_to_group table
                g2g, members.c.parent_group_id == g2g.c.member_group_id
            # stop recursing if parent_group_id is in the array of seen ids
            ).filter(~members.c.path.all(g2g.c.parent_group_id))
        )

        # SELECT from groups using our recursive ID list
        return Group.query.join(members, Group.id == members.c.parent_group_id)

listen(Group.display_name, "set", lambda gr, v, x, y: gr.slugify_name(display_name=v))
listen(Group.type, "set", lambda gr, v, x, y: gr.slugify_name(type=v))
