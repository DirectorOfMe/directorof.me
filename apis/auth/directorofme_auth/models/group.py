from sqlalchemy import Table, Column, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.sql.expression import literal, func
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.event import listen
from sqlalchemy_utils import UUIDType, generic_repr

from directorofme.authorization.groups import GroupTypes, Group as AuthGroup, Scope

from . import db

__all__ = [ "Group", "GroupTypes" ]

# through table for group -< groups
group_to_group = Table(
    db.Model.prefix_name('group_to_group'),
    db.Model.metadata,
    Column('parent_group_id', UUIDType, ForeignKey(db.Model.prefix_name('group.id')), nullable=False),
    Column('member_group_id', UUIDType, ForeignKey(db.Model.prefix_name('group.id')), nullable=False))

@generic_repr("name")
class Group(db.Model):
    '''The basic building block of access control.'''
    __tablename__ = "group"
    __table_args__ = (
        UniqueConstraint("display_name", "type"),
        UniqueConstraint("scope_name", "scope_permission"),
    )
    #: unique name of this :class:`.Group`, derived from Type/Display-Name
    name = Column(String(50), unique=True, nullable=False, index=True)

    #: user-defined name of this :class:`.Group`
    display_name = Column(String(48), nullable=False)

    #: the group type determines which authorization objects are responsible
    #: for and authorized to add this group to a session.
    #: (see :class:`.GroupTypes` for more info)
    type = Column(Enum(GroupTypes), nullable=False)

    #: all :class:`Group`s in :attr:`members` are also members of this :class:`Group`
    members = relationship(
        "Group",
        secondary=group_to_group,
        primaryjoin="Group.id == {}.c.parent_group_id".format(db.Model.prefix_name("group_to_group")),
        secondaryjoin="Group.id == {}.c.member_group_id".format(db.Model.prefix_name("group_to_group")),
        backref="member_of",
    )

    #: used by feature groups to identify a scope (realm) for discovery
    scope_name = Column(String(48), nullable=True, index=True)

    #: used by feature groups to identify the permission associated with this
    #: group/scope (realm) for discovery
    scope_permission = Column(String(46), nullable=True)

    def __init__(self, *args, **kwargs):
        '''Standard Model setup + generate a URL safe name if we have enough
           information to do so.
        '''
        super().__init__(*args, **kwargs)
        self.name = self.slugify_name()

    def slugify_name(self, **kwargs):
        '''Return a URL-friendly `name` provided an optional :param:`display_name`
           or :param:`type`.

           :param GroupType type: (optional) Group type for prefixing the name.
           :param str display_name: (optional) name to be prefixed and slugged.
        '''
        try:
            return AuthGroup(**{
                "name": self.name,
                "display_name": kwargs.get("display_name", self.display_name),
                "type": kwargs.get("type", self.type),
            }).name
        except ValueError:
            return self.name

    def scope(self):
        '''Return a scope object representing the scope and permission
           associated with this group.'''
        if self.scope_name is not None and self.scope_permission is not None:
            return Scope(name=self.scope_name, perms={
                self.scope_permission: AuthGroup.from_conforming_type(self)
            })
        return None

    @classmethod
    def scopes(cls, groups):
        '''Return a list of scopes objects for a given list of groups'''
        scopes = {}
        for group in groups:
            scope_ = group.scope()
            if scope_ is not None:
                scopes[scope_.name] = scopes.get(scope_.name, scope_).merge(scope_)

        return list(scopes.values())

    def expand(self, max_depth=None):
        '''Return a list of all groups which this group is a member of,
           recursively. This is usually done in order to flatten a list of
           groups for use by an authorization token (e.g. session) used by
           services to determine access controls cheaply at access time.

           For example, given the following groups structure:

                dom = Group(display_name="dom", type=GroupTypes.data)
                dom_employees = Group(display_name="dom-emp", type=GroupTypes.data)
                dom_employees.member_of = [dom]

                prog = Group(display_name="programmers", type=GroupTypes.data)
                dom_prog = Group(display_name="dom-programmers", type=GroupTypes.data)
                dom_prog.member_of = [dom, prog]

           Calling dom_prog.expand:

                >>> list(dom_prog.expand())

           would return the following list:

                [
                    Group(name="d-dom_prog"),
                    Group(name="d-dom-emp"),
                    Group(name="d-dom"),
                    Group(name="d-prog")
                ]

           If there is a reference-cycle:

                    everybody = Group(display_name="everybody", type=GroupTypes.data)
                    anybody = Group(display_name="anybody", type=GroupTypes.data)

                    everybody.member_of = [anybody]
                    anybody.member_of = [everybody]

           expand will detect the self-refernece and return a list with each
           group represented exactly once:

                    >>> list(anybody.expand())
                    [ Group(name="d-anybody"), Group(name="d-everybody") ]



           The code in this method is complex, but results in the execution of
           exactly one query, rather than making one call per depth. It can
           still be inefficient for deeply nested structures, so we encourage
           the API developers to set a sane default for max_depth and to avoid
           using this method outside of token setup.

           :param int max_depth: maximum amount of recursion for any group.
        '''
        g2g = aliased(group_to_group, name="g2g")
        max_depth_clause = literal(max_depth is None or max_depth > 0)
        members = db.session.query(
                # in order to make sure self is part of the set
                # we start by selecting our own id from group,
                # before recursing to group_to_group
                Group.id.label("parent_group_id"),
                # to preent infinite recursion, we track seen ids in an array
                array([Group.id]).label("path"),
            ).filter(
                # just this group
                (Group.id == self.id) & max_depth_clause
            # make a common table expression (WITH members(...) AS ())
            ).cte(name="members", recursive=True)

        # setup max depth clause
        if max_depth is not None:
            max_depth_clause = (func.array_length(members.c.path, 1) < max_depth)

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
            ).filter(~members.c.path.all(g2g.c.parent_group_id) & max_depth_clause)
        )

        # SELECT from groups using our recursive ID list
        return Group.query.join(members, Group.id == members.c.parent_group_id)


    @classmethod
    def create_scope_groups(cls, scope):
        '''Generate groups with correctly set scope attributes from an object
           conforming to the :class:`Scope` specification. The scope attributes
           help map functionality defined by programmers in code to data access
           controls implemented by authorization tokens. E.g:

                >>> Group.create_scope_groups(Scope(display_name="group"))
                [Group(name='s-group-delete'), Group(name='s-group-read'),
                 Group(name='s-group-write')]

           This method is typically used by migrations to populate concrete
           groups into the database associated with scopes that are typically
           defined in code. (either directly or via the API) E.g.:

                @scope
                class Group
                    __tablename__ = "group"
                    # ...

           Would define a scope for this Group named `group` (from the tablename),
           with 3 groups for controlling `read`, `write` and `delete` access to the
           :class:`Group` type generally. An application would then request
           access to :attr:`scope_permission` within a :attr:`scope` (e.g. it would
           ask for `read` permission in the `group` scope). If granted, the
           :class:`InstalledApp` would add all groups to an auth token for the
           :attr:`scope` and :attr:`scope_permission`s granted to the
           :class:`InstalledApp`.
        '''
        groups = []
        scope_ = Scope.from_conforming_type(scope)
        for perm_name, group in scope_.perms.items():
            groups.append(cls(
                name=group.name,
                display_name=group.display_name,
                type=group.type,
                scope_name=scope_.name,
                scope_permission=perm_name
            ))

        return groups


### Setup listeners
listen(Group.display_name, "set",
       lambda gr, v, x, y: setattr(gr, "name", gr.slugify_name(display_name=v)))
listen(Group.type, "set",
       lambda gr, v, x, y: setattr(gr, "name", gr.slugify_name(type=v)))
