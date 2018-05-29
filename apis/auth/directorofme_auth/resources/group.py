import functools
import collections

from flask_restful import abort
from sqlalchemy.exc import IntegrityError
from directorofme.flask.api import dump_with_schema, load_with_schema, with_pagination_params, first_or_abort,\
                                   load_query_params, Resource

from . import api, schemas
from .. import models, spec, db

@spec.register_resource
@api.resource("/groups/<string:name>", endpoint="groups_api")
class Group(Resource):
    """
    An endpoint for retrieving and manipulating groups
    """
    @dump_with_schema(schemas.GroupSchema)
    def get(self, name):
        """
        ---
        description: Retrieve a group by slug.
        parameters:
            - api_version
            - name: name
              type: string
              description: slugified group name.
              in: path
        responses:
            200:
                description: Successfully retrieve a Group
                schema: GroupSchema
            404:
                description: Could not find a Group with current access level.
                schema: ErrorSchema
        """
        return first_or_abort(models.Group.query.filter(models.Group.name == name))

    @load_with_schema(schemas.GroupSchema)
    @dump_with_schema(schemas.GroupSchema)
    def put(self, group_data, name):
        """
        ---
        description: Update a group in it's entirety.
        parameters:
            - api_version
            - name: name
              type: string
              description: slugified group name.
              in: path
            - in: body
              schema: GroupSchema
              description: Data to create the group type with.
              name: group
        responses:
            200:
                description: Successfully update a Group
                schema: GroupSchema
            301:
                description: Update which caused the name to change.
                schema: GroupSchema
                headers:
                    Location:
                        description: new URL for the updated Group.
                        type: string
                        format: url
            400:
                description: Validation error on save or in request body.
                schema: ErrorSchema
            403:
                description: No permission to update this Group object.
                schema: ErrorSchema
            404:
                description: Could not find existing Group for name.
                schema: ErrorSchema
        """
        return self.generic_update(db, api, models.Group, "name", name, group_data)

    @load_with_schema(schemas.GroupSchema, partial=True)
    @dump_with_schema(schemas.GroupSchema)
    def patch(self, group_data, name):
        """
        ---
        description: Partially update a Group.
        parameters:
            - api_version
            - name: name
              type: string
              description: slugified group name.
              in: path
            - in: body
              schema: GroupSchema
              description: Data to create the group type with.
              name: group
        responses:
            200:
                description: Successfully update a Group
                schema: GroupSchema
            301:
                description: Update which caused the name to change.
                schema: GroupSchema
                headers:
                    Location:
                        description: new URL for the updated Group.
                        type: string
                        format: url
            400:
                description: Validation error on save or in request body.
                schema: ErrorSchema
            403:
                description: No permission to update this Group object.
                schema: ErrorSchema
            404:
                description: Could not find existing Group for name.
                schema: ErrorSchema
        """
        return self.generic_update(db, api, models.Group, "name", name, group_data)

    def delete(self, name):
        """
        ---
        description: Delete a Group
        parameters:
            - api_version
            - name: name
              type: string
              description: slugified group name.
              in: path
        responses:
            204:
                description: Group deleted.
            403:
                description: No permission to delete this Group object.
                schema: ErrorSchema
            404:
                description: Could not find existing Group for slug.
                schema: ErrorSchema
        """
        return self.generic_delete(db, models.Group, "name", name)


def dump_by_list_name(**named_schemas):
    @functools.wraps(dump_by_list_name)
    def inner(fn):
        @functools.wraps(fn)
        def inner_inner(*args, name, list_name,**kwargs):
            if list_name not in ("members", "member_of"):
                abort(400, "Invalid membership list name, must be either `members` or `member_of`")
            return dump_with_schema(named_schemas[list_name])(fn)(*args, name, list_name, **kwargs)

        return inner_inner

    return inner

### TODO: Factor to one /groups/<name>/<list_type> class
@spec.register_resource
@api.resource("/groups/<name>/<list_name>", endpoint="groups_api:list")
class GroupMembersOrMemberOfList(Resource):
    @dump_by_list_name(members=schemas.GroupMembersSchema, member_of=schemas.GroupMemberOfSchema)
    def get(self, name, list_name):
        """
        ---
        description: Get the Groups which are members of this group
        parameters:
            - api_version
            - name: name
              type: string
              description: slugified group name.
              in: path
            - name: list_type
              description: Either members or member_of.
        responses:
            200:
                description: Successfully retrieve the collection of Member Group objects.
                schema: GroupMembersSchema
            404:
                description: Parent group cannot be found
                schema: ErrorSchema
        """
        return first_or_abort(models.Group.query.filter(models.Group.name == name))

    @load_with_schema(schemas.GroupSchema)
    @dump_by_list_name(members=schemas.GroupMembersSchema, member_of=schemas.GroupMemberOfSchema)
    def post(self, new_group_data, name, list_name):
        """
        ---
        description: Append a new or existing group to the members list for a Group
        parameters:
            - api_version
            - name: list_type
              description: Either members or member_of.
            - in: body
              schema: GroupMembersSchema
              description: Group to append to the members list.
              name: group_data
        responses:
            200:
                description: Successfully append an existing Group to this members list.
                schema:
                  oneOf:
                    - GroupMembersSchema
                    - GroupMemberOfSchema
            201:
                description: Successfully created a new Group and appended it to the members list.
                schema:
                  oneOf:
                    - GroupMembersSchema
                    - GroupMemberOfSchema
                headers:
                    Location:
                        description: URL for the newly created Group.
                        type: string
                        format: url
            400:
                description: Validation Error when creating the new Group.
                schema: ErrorSchema
            403:
                description: No permission to create a new Group object.
                schema: ErrorSchema
            404:
                description: Cannot access parent or child object.
                schema: ErrorSchema
        """
        target = first_or_abort(models.Group.query.filter(models.Group.name == name))
        new_obj, status_code = models.Group(**new_group_data), 201

        existing_obj = models.Group.query.filter(models.Group.name == new_obj.name).first()
        if existing_obj:
            new_obj, status_code = existing_obj, 200

        getattr(target, list_name).append(new_obj)

        db.session.add(target, new_obj)
        db.session.commit()

        headers = {}
        if status_code == 201:
            headers = { "Location": api.url_for(Group, name=new_obj.name) }

        return target, status_code, headers



    @load_with_schema(schemas.GroupSchema)
    @dump_by_list_name(members=schemas.GroupMembersSchema, member_of=schemas.GroupMemberOfSchema)
    def delete(self, group_data, name, list_name):
        """
        ---
        description: Remove a groups as a member of another group.
        parameters:
            - api_version
            - name: list_type
              description: Either members or member_of.
            - name: name
              type: string
              description: slugified group name.
              in: path
            - in: body
              schema: GroupSchema
              description: Data to remove the Group using
              name: group
        responses:
            200:
                description: Successfully update a Group's member list
                schema:
                  oneOf:
                    - GroupMembersSchema
                    - GroupMemberOfSchema
            400:
                description: Validation error on saving new Group in `list_type` list.
                schema: ErrorSchema
            403:
                description: No permission to update this Group object.
                schema: ErrorSchema
            404:
                description: Could not find existing Group for name.
                schema: ErrorSchema
        """
        target = first_or_abort(models.Group.query.filter(models.Group.name == name))
        remove = models.Group(**group_data)
        setattr(target, list_name, [m for m in getattr(target, list_name) if target.name != remove.name])
        return self.generic_update(db, api, models.Group, "name", name, {
            list_name: [m for m in getattr(target, list_name) if m.name != remove.name]
        })


    @dump_by_list_name(members=schemas.GroupMembersSchema, member_of=schemas.GroupMemberOfSchema)
    def put(self, name, list_name):
        """
        ---
        description: Update a grouplist for a group in it's entirety with existing or new groups.
        parameters:
            - api_version
            - name: list_type
              description: Either members or member_of.
            - name: name
              type: string
              description: slugified group name.
              in: path
            - in: body
              schema: GroupMembersSchema
              description: Data to create the group type with.
              name: group
        responses:
            200:
                description: Successfully update a Group's member list
                schema:
                  oneOf:
                    - GroupMembersSchema
                    - GroupMemberOfSchema
            400:
                description: Validation error on saving new Group in `list_type` list.
                schema: ErrorSchema
            403:
                description: No permission to update this Group object.
                schema: ErrorSchema
            404:
                description: Could not find existing Group for name.
                schema: ErrorSchema
        """
        @load_with_schema(schemas.GroupMembersSchema if list_name == "members" else schemas.GroupMemberOfSchema)
        def inner(collection_data):
            collection_map = collections.OrderedDict()
            for d in collection_data[list_name]:
                obj = models.Group(**d)
                collection_map[obj.name] = obj

            for o in models.Group.query.filter(models.Group.name.in_([g.name for g in collection_map.values()])):
                collection_map[o.name] = o

            return self.generic_update(db, api, models.Group, "name", name,
                                       { list_name: list(collection_map.values()) })

        return inner()


@spec.register_resource
@api.resource("/groups/", endpoint="groups_collection_api")
class Groups(Resource):
    @dump_with_schema(schemas.GroupCollectionSchema)
    @with_pagination_params()
    @load_query_params(schemas.GroupCollectionQuerySchema)
    def get(self, page=1, results_per_page=50, type=None, scope_name=None):
        """
        ---
        description: Get a colleciton of groups.
        parameters:
            - api_version
            - page
            - results_per_page
            - name: type
              type: string
              description: "GroupType to filter by (one of: `system`, `scope`, `feature`, `data`)."
            - name: scope_name
              type: string
              description: Return all groups for a given scope.
        responses:
            200:
                description: Successfully retrieve a collection of Group objects.
                schema: GroupCollectionSchema
            400:
                description: An invalid value was sent for a parameter (usually an incorrect type).
                schema: ErrorSchema
        """
        query = models.Group.query
        for (val, col) in ((type, models.Group.type), (scope_name, models.Group.scope_name)):
            if val is not None:
                query = query.filter(col == val)

        return self.paged(query, page, results_per_page, models.Group.created, type=type,
                          scope_name=scope_name)

    @load_with_schema(schemas.GroupSchema)
    @dump_with_schema(schemas.GroupSchema)
    def post(self, group_data):
        """
        ---
        description: Create a new event type.
        parameters:
            - api_version
            - in: body
              schema: GroupSchema
              description: Data to create the group type with.
              name: group_data
        responses:
            201:
                description: Successfully created the new object.
                schema: GroupSchema
                headers:
                    Location:
                        description: URL for the newly created Group.
                        type: string
                        format: url
            400:
                description: Validation Error when creating the new object.
                schema: ErrorSchema
            403:
                description: No permission to create a new Group object.
                schema: ErrorSchema
        """
        return self.generic_insert(db, api, models.Group, group_data, "name", url_cls=Group)
