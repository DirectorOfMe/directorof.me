from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Sequence
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy_utils import JSONType, UUIDType

from directorofme.orm import slugify_on_change
from directorofme.flask import Model

__all__ = [ "EventType", "Event" ]

#TODO: hook up to app
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

    #: for polling
    cursor = Column(Integer, Sequence("event_cursor_seq"), nullable=False)

    #: id of the :class:`.EventType` this :class:`Event` is.
    event_type_id = Column(UUIDType, ForeignKey(EventType.id), nullable=False)

    #: type of :class:`.EventType` this :class:`.Event` is.
    event_type = relationship(EventType)

    #: time the :class:`.Event` occured
    event_time = Column(DateTime, nullable=False, default=func.now())

    #: config for this event (conforms to :attr:`.Event.data_schema`)
    data = Column(JSONType)

    @property
    def event_type_slug(self):
        return self.event_type.slug
