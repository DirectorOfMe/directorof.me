import enum
from ..specify import Spec, Attribute

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

class Group(Spec):
    name = Attribute(str)
    display_name = Attribute(str)
    type = Attribute(GroupTypes)
