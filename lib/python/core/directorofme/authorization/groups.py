import enum

import slugify

from ..specify import Spec, Attribute
from ..authorization import standard_permissions

__all__ = [ "GroupTypes", "Group", "Scope", "scope" ]

class GroupTypes(enum.Enum):
    '''GroupTypes defines the three types of group that are available. Groups
       determine access control by virue of being added to a groups list in
       the user's active session. The type of group determines which active
       authorization objects may add a particular group to a session.

       - A group with type :attr:`.scope` controls access to data by type. This
         type of group is added to a session by the active
         :attr:`InstalledApp.app` for this session, which the user has
         previously authorized to access these scopes.
       - A group with type :attr:`.feature` would be added to a session by an
         active :class:`License` for this session.
       - A group with type :attr:`.data` would be added to the session by
         a :class:`Profile` (essentially a user-defined group).
    '''
    system = '0'
    scope = 's'
    feature = 'f'
    data = 'd'

### TODO: docs
class Group(Spec):
    name = Attribute(str, default=None)
    display_name = Attribute(str)
    type = Attribute(GroupTypes)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # will throw if name is not set and either display name or type are not set
        self.name = self.generate_name()

    def generate_name(self):
        if self.name is None:
            return slugify.slugify("{}-{}".format(self.type.value, self.display_name))
        return self.name


class Scope(Spec):
    name = Attribute(str, default=None)
    display_name = Attribute(str)

    __perms__ = Attribute(tuple, default=standard_permissions)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = self.generate_name()
        self.perms = {}

        for perm_name in self.__perms__:
            self.perms[perm_name] = Group(
                display_name=self.perm_name(perm_name),
                type=GroupTypes.scope
            )

    def __getattr__(self, attr):
        try:
            return self.perms[attr]
        except KeyError:
            raise AttributeError(attr)

    def generate_name(self):
        if self.name is None:
            return slugify.slugify(self.display_name)
        return self.name

    def perm_name(self, perm_name):
        return slugify.slugify("{}-{}".format(self.name, perm_name))


def scope(scope_name_or_cls):
    scope_name = scope_name_or_cls
    if callable(scope_name_or_cls):
        scope_name = getattr(
            scope_name_or_cls,
            "__tablename__",
            scope_name_or_cls.__name__
        )

        # recurse
        return scope(scope_name)(scope_name_or_cls)

    new_scope = Scope(display_name=scope_name)
    scope.known_scopes.setdefault(new_scope.name, new_scope)
    ###: TODO hook this up to do authorization things
    def inner(cls):
        return cls
    return inner

scope.known_scopes = {}
