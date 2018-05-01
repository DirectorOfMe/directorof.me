import functools

import flask
from flask_restful import Resource, abort

from directorofme.flask.api import dump_with_schema, with_pagination_params

from . import models, marshmallow, spec, api

@spec.register_resource
@api.resource("/event_types/<string:slug>", endpoint="event_types_api")
class EventType(Resource):
    """
    An endpoint for retrieving and manipulating event type definitions.
    """
    @spec.register_schema("EventType")
    class EventTypeSchema(marshmallow.Schema):
        slug = marshmallow.String(required=True)
        name = marshmallow.String(required=True)
        desc = marshmallow.String(required=True)
        data_schema = marshmallow.Dict()

        _links = marshmallow.Hyperlinks({
            "self": marshmallow.URLFor("event.event_types_api", slug="<slug>"),
            "collection": marshmallow.URLFor("event.event_types_collection_api"),
        })

    @dump_with_schema(EventTypeSchema)
    def get(self, slug):
        """
        ---
        description: Retrieve an event type definition by slug.
        parameters:
            - api_version
            - name: slug
              in: path
              description: Unique name for this EventType (derived from name)
              type: string
        responses:
            200:
                description: Successfully retrieve an EventType
                schema: EventTypeSchema
            404:
                description: Could not find an EventType with current access level.
                schema: ErrorSchema
        """
        return models.EventType.query.filter(models.EventType.slug == slug).first()


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

        collection = marshmallow.Nested(EventType.EventTypeSchema, many=True)
        _links = marshmallow.Hyperlinks({
            "self": marshmallow.URLFor("event.event_types_collection_api",
                                       page="<page>", results_per_page="<results_per_page"),
            "next": marshmallow.URLFor("event.event_types_collection_api",
                                       page="<next_page>", results_per_page="<results_per_page"),
            "prev": marshmallow.URLFor("event.event_types_collection_api",
                                       page="<prev_page>", results_per_page="<results_per_page"),
        })

    @dump_with_schema(EventTypeCollectionSchema)
    @with_pagination_params(marshmallow)
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
            404:
                description: Could not find an EventType with current access level.
                schema: ErrorSchema
        """
        objs = models.EventType.query.filter().limit(results_per_page).offset((page - 1) * results_per_page).all()

        return {
            "page": page,
            "next_page": page + (1 if len(objs) >= results_per_page else 0),
            "prev_page": max(page - 1, 1),
            "results_per_page": results_per_page,
            "collection": objs,
        }


@api.resource("/swagger.json", endpoint="spec_api")
class Spec(Resource):
    def get(self):
        return spec.to_dict()

#@resource_url(api, "/events/", endpoint="events_collection_api")
#class Event(Resource):
#    pass
#
#@resource_url(api, "/event/<string:id>", endpoint="events_api")
#class Events(Resource):
#    pass
