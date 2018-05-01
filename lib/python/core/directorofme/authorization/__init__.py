'''
directorofme.authorization -- shared libraries for authorizing access to
                              functionality and data.
'''

__all__ = [ "groups", "session", "exceptions", "standard_permissions", "requires", "orm" ]

standard_permissions = ( "read", "write", "delete" )

### ORDER MATTERS HERE -- SOME MODULES DEPEND ON OTHERS
from . import exceptions
from . import groups
from . import session
from . import requires
from . import orm
