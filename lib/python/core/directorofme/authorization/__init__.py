import enum

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

import session
import jwt
