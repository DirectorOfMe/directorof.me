import functools

import flask
from flask_restful import Resource, abort

from directorofme.flask.api import dump_with_schema, load_with_schema, with_pagination_params, \
                                   uuid_or_abort, first_or_abort, load_query_params, with_cursor_params
from directorofme.authorization.exceptions import PermissionDeniedError
from directorofme.authorization import session
from sqlalchemy.exc import IntegrityError

from . import models, db, marshmallow, spec, api

@spec.register_resource
@api.resource("/event_types/<string:slug>", endpoint="event_types_api")
class EventType(Resource):
    """
    An endpoint for retrieving and manipulating event type definitions.
    """
    @spec.register_schema("EventTypeRequest")
    class EventTypeRequestSchema(marshmallow.Schema):
        name = marshmallow.String(required=True)
        desc = marshmallow.String(required=True)
        data_schema = marshmallow.Dict()

    @spec.register_schema("EventTypeResponse")
    class EventTypeResponseSchema(EventTypeRequestSchema):
        slug = marshmallow.String(required=True)
        created = marshmallow.DateTime()
        updated = marshmallow.DateTime()

        _links = marshmallow.Hyperlinks({
            "self": marshmallow.URLFor("event.event_types_api", slug="<slug>"),
            "collection": marshmallow.URLFor("event.event_types_collection_api"),
        })

    @dump_with_schema(EventTypeResponseSchema)
    def get(self, slug):
        """
        ---
        description: Retrieve an event type definition by slug.
        parameters:
            - api_version
            - slug
        responses:
            200:
                description: Successfully retrieve an EventType
                schema: EventTypeResponseSchema
            404:
                description: Could not find an EventType with current access level.
                schema: ErrorSchema
        """
        return first_or_abort(models.EventType.query.filter(models.EventType.slug == slug))


    @load_with_schema(EventTypeRequestSchema)
    @dump_with_schema(EventTypeResponseSchema)
    def put(self, event_type_data, slug):
        """
        ---
        description: Update an event type in it's entirety.
        parameters:
            - api_version
            - slug
            - in: body
              schema: EventTypeRequestSchema
              description: Data to update the event type with.
              name: event_type
        responses:
            200:
                description: Successfully update an EventType
                schema: EventTypeResponseSchema
            301:
                description: Update which caused the slug to change.
                schema: EventTypeResponseSchema
                headers:
                    Location:
                        description: new URL for the updated EventType.
                        type: string
                        format: url
            400:
                description: Validation error on save or in request body.
                schema: ErrorSchema
            401:
                description: No permission to update this EventType object.
                schema: ErrorSchema
            404:
                description: Could not find existing EventType for slug.
                schema: ErrorSchema
        """
        return self._update(event_type_data, slug)

    @load_with_schema(EventTypeRequestSchema, partial=True)
    @dump_with_schema(EventTypeResponseSchema)
    def patch(self, event_type_data, slug):
        """
        ---
        description: Partially update an event type
        parameters:
            - api_version
            - slug
            - in: body
              schema: EventTypeRequestSchema
              description: Data to update the event type with.
              name: event_type
        responses:
            200:
                description: Successfully update an EventType
                schema: EventTypeResponseSchema
            301:
                description: Update which caused the slug to change.
                schema: EventTypeResponseSchema
                headers:
                    Location:
                        description: new URL for the updated EventType.
                        type: string
                        format: url
            400:
                description: Validation error on save or in request body.
                schema: ErrorSchema
            401:
                description: No permission to update this EventType object.
                schema: ErrorSchema
            404:
                description: Could not find existing EventType for slug.
                schema: ErrorSchema
        """
        return self._update(event_type_data, slug)

    def _update(self, event_type_data, slug):
        """Post/Patch helper"""
        event_type = first_or_abort(models.EventType.query.filter(models.EventType.slug == slug))
        orig_slug = event_type.slug
        for k,v in event_type_data.items():
            setattr(event_type, k, v)

        try:
            db.session.add(event_type)
            db.session.commit()
        except IntegrityError:
            abort(400, message="Please choose a unique name or slug")

        if event_type.slug != orig_slug:
            return event_type, 301, { "Location": api.url_for(EventType, slug=event_type.slug) }
        return event_type

    def delete(self, slug):
        """
        ---
        description: Delete an EventType
        parameters:
            - api_version
            - slug
        responses:
            204:
                description: EventType deleted.
            401:
                description: No permission to delete this EventType object.
                schema: ErrorSchema
            404:
                description: Could not find existing EventType for slug.
                schema: ErrorSchema
        """
        db.session.delete(first_or_abort(models.EventType.query.filter(models.EventType.slug == slug)))
        db.session.commit()
        return None, 204


@spec.register_resource
@api.resource("/event_types/", endpoint="event_types_collection_api")
class EventTypes(Resource):
    """
    An endpoint for retrieving and manipulating collections of event types.
    """
    @spec.register_schema("EventTypeCollection")
    class EventTypeCollectionSchema(marshmallow.Schema):
        page = marshmallow.Integer()
        results_per_page = marshmallow.Integer()

        collection = marshmallow.Nested(EventType.EventTypeResponseSchema, many=True)
        _links = marshmallow.Hyperlinks({
            "self": marshmallow.URLFor("event.event_types_collection_api",
                                       page="<page>", results_per_page="<results_per_page>"),
            "next": marshmallow.URLFor("event.event_types_collection_api",
                                       page="<next_page>", results_per_page="<results_per_page>"),
            "prev": marshmallow.URLFor("event.event_types_collection_api",
                                       page="<prev_page>", results_per_page="<results_per_page>"),
        })

    @dump_with_schema(EventTypeCollectionSchema)
    @with_pagination_params()
    def get(self, page=1, results_per_page=50):
        """
        ---
        description: Retrieve a collection of event types.
        parameters:
            - api_version
            - page
            - results_per_page
        responses:
            200:
                description: Successfully retrieve an EventType
                schema: EventTypeCollectionSchema
            400:
                description: An invalid value was sent for a parameter.
                schema: ErrorSchema
        """
        objs = models.EventType.query\
                    .order_by(models.EventType.created)\
                    .limit(results_per_page + 1)\
                    .offset((page - 1) * results_per_page)\
                    .all()

        extra = objs.pop() if len(objs) > results_per_page else None
        return {
            "page": page,
            "next_page": page + (1 if extra else 0),
            "prev_page": max(page - 1, 1),
            "results_per_page": results_per_page,
            "collection": objs,
        }


    @load_with_schema(EventType.EventTypeRequestSchema)
    @dump_with_schema(EventType.EventTypeResponseSchema)
    def post(self, event_type_data):
        """
        ---
        description: Create a new event type.
        parameters:
            - api_version
            - in: body
              schema: EventTypeRequestSchema
              description: Data to create the event type with.
              name: event_type
        responses:
            201:
                description: Successfully created the new object.
                schema: EventTypeResponseSchema
                headers:
                    Location:
                        description: URL for the newly created EventType.
                        type: string
                        format: url
            400:
                description: Validation Error when creating the new object.
                schema: ErrorSchema
            401:
                description: No permission to create a new EventType object.
                schema: ErrorSchema
        """
        try:
            new_obj = models.EventType(**event_type_data)
            db.session.add(new_obj)
            db.session.commit()
            return new_obj, 201, { "Location": api.url_for(EventType, slug=new_obj.slug) }
        except IntegrityError:
            abort(400, message="Please choose a unique name or slug")


@api.resource("/events/<string:uuid>", endpoint="events_api")
class Event(Resource):
    @spec.register_schema("EventRequest")
    class EventRequestSchema(marshmallow.Schema):
        event_type_slug = marshmallow.String(required=True)
        event_time = marshmallow.DateTime()
        data = marshmallow.Dict(required=True)


    @spec.register_schema("EventResponse")
    class EventResponseSchema(EventRequestSchema):
        id = marshmallow.UUID(required=True)
        created = marshmallow.DateTime(required=True)
        updated = marshmallow.DateTime(required=True)

        event_time = marshmallow.DateTime(required=True)

        _links = marshmallow.Hyperlinks({
            "self": marshmallow.URLFor("event.events_api", uuid="<id>"),
            "collection": marshmallow.URLFor("event.events_collection_api"),
            "event_type": marshmallow.URLFor("event.event_types_api", slug="<event_type_slug>"),
        })

    @dump_with_schema(EventResponseSchema)
    def get(self, uuid):
        """
        ---
        description: Retrieve an event by id.
        parameters:
            - api_version
            - uuid
        responses:
            200:
                description: Successfully retrieve an Event
                schema: EventTypeResponseSchema
            400:
                description: Invalid uuid.
                schema: ErrorSchema
            404:
                description: Could not find an EventType with current access level.
                schema: ErrorSchema
        """
        return first_or_abort(models.Event.query.filter(models.Event.id == uuid_or_abort(uuid)))

    def delete(self, uuid):
        """
        description: Delete an Event
        parameters:
            - api_version
            - uuid
        responses:
            204:
                description: Event deleted.
            401:
                description: No permission to delete this Event object.
                schema: ErrorSchema
            404:
                description: Could not find existing EventType for uuid.
                schema: ErrorSchema
        """
        db.session.delete(first_or_abort(models.Event.query.filter(models.Event.id == uuid_or_abort(uuid))))
        db.session.commit()
        return None, 204


@api.resource("/events/", endpoint="events_collection_api")
class Events(Resource):
    @spec.register_schema("EventCollection")
    class EventCollectionSchema(marshmallow.Schema):
        results_per_page = marshmallow.Integer()
        collection = marshmallow.Nested(Event.EventResponseSchema, many=True)

        _links = marshmallow.Hyperlinks({
            "self": marshmallow.URLFor("event.events_collection_api",
                                       event_type_slug="<event_type_slug>",
                                       since_id="<since_id>", max_id="<max_id>",
                                       results_per_page="<results_per_page>"),
            "next": marshmallow.URLFor("event.events_collection_api",
                                       event_type_slug="<event_type_slug>",
                                       since_id="<next_since_id>", max_id="<next_max_id>",
                                       results_per_page="<results_per_page>"),
            "prev": marshmallow.URLFor("event.events_collection_api",
                                       event_type_slug="<event_type_slug>",
                                       since_id="<prev_since_id>", max_id="<prev_max_id>",
                                       results_per_page="<results_per_page>"),
        })

    @spec.register_schema("EventCollectionQuery")
    class EventCollectionQuerySchema(marshmallow.Schema):
        event_type_slug = marshmallow.String()

    @dump_with_schema(EventCollectionSchema)
    @with_cursor_params()
    @load_query_params(EventCollectionQuerySchema)
    def get(self, results_per_page=50, event_type_slug=None, since_id=None, max_id=None):
        """
        ---
        description: Retrieve a collection of event types.
        parameters:
            - api_version
            - results_per_page
            - in: query
              name: event_type_slug
              type: string
              description: slug of event_type this event conforms to.
            - in: query
              name: since_id
              type: string
              format: uuid
              description: get all events since this event
            - in: query
              name: max_id
              type: string
              format: uuid
              description: get all events prior to and including this event
        responses:
            200:
                description: Successfully retrieve an EventType
                schema: EventTypeCollectionSchema
            400:
                description: An invalid value was sent for a parameter.
                schema: ErrorSchema
            404:
                description: No EventType for provided event_type_slug, or Event for provided last_seen_id.
                schema: ErrorSchema
        """
        results_per_page = min(max(results_per_page, 1), 50)

        query = models.Event.query
        if since_id:
            #factor down to one query
            after = first_or_abort(models.Event.query.filter(models.Event.id == since_id))
            query = query.filter(models.Event.cursor > after.cursor)
        elif max_id:
            before = first_or_abort(models.Event.query.filter(models.Event.id == max_id))
            query = query.filter(models.Event.cursor <= before.cursor)
        if event_type_slug:
            query = query.join(models.Event.event_type).filter(models.EventType.slug == event_type_slug)

        order_by = models.Event.cursor
        step = 1
        extra = 0
        if max_id and not since_id:
            order_by = order_by.desc()
            step = -1
            extra = 1


        objs = query.order_by(order_by).limit(results_per_page + extra).all()[::step]

        if max_id and not since_id and len(objs) == results_per_page + extra:
            since_id = objs[0].id
            objs = objs[1:]

        return {
            # self query params
            "event_type_slug": event_type_slug,
            "since_id": since_id,
            "max_id": max_id,
            "results_per_page": results_per_page,

            # next query params
            "next_since_id": objs[-1].id if objs else since_id,
            "next_max_id": None,

            # prev query params
            "prev_since_id": None,
            "prev_max_id": since_id,

            # results
            "collection": objs,
        }

    @load_with_schema(Event.EventRequestSchema)
    @dump_with_schema(Event.EventResponseSchema)
    def post(self, event_data):
        """
        ---
        description: Create a new event.
        parameters:
            - api_version
            - in: body
              schema: EventRequestSchema
              description: Data to create the event with.
              name: event
        responses:
            201:
                description: Successfully created the new object.
                schema: EventResponseSchema
                headers:
                    Location:
                        description: URL for the newly created Event.
                        type: string
                        format: url
            400:
                description: Validation Error when creating the new object.
                schema: ErrorSchema
            401:
                description: No permission to create a new Event object.
                schema: ErrorSchema
            404:
                description: No event_type for event_type_slug.
        """
        event_data["event_type"] = first_or_abort(
            models.EventType.query.filter(models.EventType.slug == event_data.pop("event_type_slug"))
        )

        new_obj = models.Event(**event_data)
        db.session.add(new_obj)
        db.session.commit()
        return new_obj, 201, { "Location": api.url_for(Event, uuid=new_obj.id) }
