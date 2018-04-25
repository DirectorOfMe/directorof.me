from sqlalchemy import Table, Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.event import listen
from sqlalchemy_utils import URLType, JSONType, UUIDType
from slugify import slugify

from directorofme.authorization.orm import slugify_on_change
from directorofme.authorization.flask import Model

__all__ = [ "EventType", "Event" ]

#TODO: hook up to perms
#TODO: hook up to app
#TODO: tests

@slugify_on_change("name", "slug")
class EventType(Model):
    '''Table defining an event type which emitted events are expected to
       conform to. Right now this is convention, but eventually the schema
       will be enforced.

       Users of the events API are free to use this schema for their own validation / app building
   '''
    __tablename__ = "event_type"

    #: unique, user-defined name of this EventType
    name = Column(String(50), unique=True, nullable=False)

    #: unique, url-safe name used to fetch :class:`.EventType` objects from the API
    slug = Column(String(50), index=True, unique=True, nullable=False)

    #: user-defined description of this event type.
    desc = Column(String(255), nullable=False)

    #: JSON Schema defining the expected format for :class:`.Event` data.
    data_schema = Column(JSONType)


class Event(Model):
    __tablename__ = "event"

    #: id of the :class:`.EventType` this :class:`Event` is.
    event_type_id = Column(UUIDType, ForeignKey(EventType.id), nullable=False)

    #: type of :class:`.EventType` this :class:`.Event` is.
    event_type = relationship(EventType)

    #: time the :class:`.Event` occured
    event_time = Column(DateTime, nullable=False)

    #: config for this event (conforms to :attr:`.Event.data_schema`)
    data = Column(JSONType)
