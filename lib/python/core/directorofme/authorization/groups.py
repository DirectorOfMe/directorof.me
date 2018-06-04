import enum

import slugify

from ..specify import Spec, Attribute
from ..authorization import standard_permissions

__all__ = [ "GroupTypes", "Group", "Scope", "root", "admin", "nobody", "everybody", "anybody",
            "user", "staff", "push", "base_groups" ]

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

    def __json_encode__(self):
        return self.name


### TODO: docs
class Group(Spec):
    name = Attribute(str, default=None)
    display_name = Attribute(str)
    type = Attribute(GroupTypes)

    def __init__(self, **kwargs):
        type_ = kwargs.get("type")
        if isinstance(type_, str):
            try:
                kwargs["type"] = getattr(GroupTypes, type_)
            except AttributeError:
                raise ValueError("Invalid type `{}`".format(type_))

        super().__init__(**kwargs)

        # will throw if name is not set and either display name or type are not set
        self.name = self.generate_name()

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Group):
            return NotImplemented
        return hash(self) == hash(other)

    def __ne__(self, other):
        ret = self.__eq__(other)
        return ret if ret is NotImplemented else not ret

    def generate_name(self):
        if self.name is None:
            try:
                return slugify.slugify("-".join([self.type.value, self.display_name]))
            except (AttributeError, TypeError):
                raise ValueError("generate name failed for type: {}, display_name:"\
                                 " {}".format(self.type, self.display_name))
        return self.name


class Scope(Spec):
    name = Attribute(str, default=None)
    display_name = Attribute(str)

    perms = Attribute(dict)
    __perms__ = Attribute(tuple, default=standard_permissions)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = self.generate_name()
        try:
            self.__perms__ = tuple(self.perms.keys())
        except ValueError:
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


    def merge(self, other):
        if self.name != other.name:
            raise ValueError(
                "Cannot merge scopes with mis-matched names:"\
                " '{}'/'{}'".format(self.name, other.name)
            )

        new_kwargs = { "perms": self.perms.copy(), "name": self.name }
        new_kwargs["perms"].update(other.perms)

        # other wins to stay consistent with perms behavior
        for obj in (other, self):
            try:
                new_kwargs["display_name"] = obj.display_name
                break
            except ValueError:
                pass

        # return a new scope
        return self.__class__(**new_kwargs)

### Pre-defined groups
root = Group(display_name="root", type=GroupTypes.system)
admin = Group(display_name="admin", type=GroupTypes.system)
nobody = Group(display_name="nobody", type=GroupTypes.system)
everybody = anybody = Group(display_name="everybody", type=GroupTypes.system)
user = Group(display_name="user", type=GroupTypes.feature)
staff = Group(display_name="staff", type=GroupTypes.feature)

push = Group(display_name="push", type=GroupTypes.system)

base_groups = [ root, admin, nobody, everybody, user, staff, push ]
