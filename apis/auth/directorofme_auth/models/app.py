from sqlalchemy import Table, Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import URLType, JSONType, UUIDType

from directorofme.orm import slugify_on_change
from directorofme.authorization.groups import Group as AuthGroup
from directorofme.flask import Model

from . import Group

__all__ = [ "App", "InstalledApp" ]

requested_access_groups = Table(
    Model.prefix_name('requested_scopes'),
    Model.metadata,
    Column('app_id', UUIDType, ForeignKey(Model.prefix_name('app.id')), nullable=False),
    Column('group_id', UUIDType, ForeignKey(Model.prefix_name('group.id')), nullable=False))

granted_access_groups = Table(
    Model.prefix_name('granted_scopes'),
    Model.metadata,
    Column('installed_app_id', UUIDType, ForeignKey(Model.prefix_name('installed_app.id')), nullable=False),
    Column('group_id', UUIDType, ForeignKey(Model.prefix_name('group.id')), nullable=False))

@slugify_on_change("name", "slug")
class App(Model):
    '''An App is an application that can be installed and run on the DOM
       platform as an :class:`.InstalledApp`.
    '''
    __tablename__ = "app"

    #: unique, user-defined name of this Application
    name = Column(String(50), unique=True, nullable=False)

    #: unique, url-safe name used to fetch :class:`.App` objects from the API
    slug = Column(String(50), index=True, unique=True, nullable=False)

    #: user-defined description fo this app.
    desc = Column(String(255), nullable=False)

    #: Informational URL for this application.
    url = Column(URLType, nullable=False)

    #: OAuth callback URL.
    callback_url = Column(URLType)

    #: JSON Schema defining the expected format for :class:`.InstalledApp` config.
    config_schema = Column(JSONType)

    #: Groups this app would like to add into the session
    requested_access_groups = relationship("Group", secondary=requested_access_groups, backref="requested_by")

    @property
    def requested_scopes(self):
        return Group.scopes(self.requested_access_groups)


class InstalledApp(Model):
    '''InstalledApp is an instance of :class:`.App` that has been installed
       and is running on the DOM platform.

       NB: There is no explicit relationship between a user or license and a
       list of available apps. The list of available installed apps is simply
       the list of available installed apps that the current session has read
       access to (via it's active groups).
    '''
    __tablename__ = "installed_app"

    #: id of :attr:`.app` associated with this instance
    app_id = Column(UUIDType, ForeignKey(App.id), nullable=False)

    #: type of :class:`.App` this :class:`.InstalledApp` is.
    app = relationship(App)

    #: config for this app (conforms to :attr:`.App.config_schema`)
    config = Column(JSONType)

    #: Groups this app will mix into session
    access_groups = relationship("Group", secondary=granted_access_groups, backref="granted_to")

    @property
    def app_name(self):
        return self.app.name

    @property
    def scopes(self):
        return Group.scopes(self.access_groups)

    @classmethod
    def install_for_group(cls, app, group, config=None, access_groups=None, **perms):
        if access_groups is None:
            access_groups = app.requested_access_groups

        if isinstance(group, Group) or isinstance(group, AuthGroup):
            group = group.name

        reads = perms.get("read", tuple()) + (group,)
        return cls(app=app, read=reads, config=config, access_groups=access_groups, **perms)
