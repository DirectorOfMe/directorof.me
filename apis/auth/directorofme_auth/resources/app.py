import copy
import jsonschema
from Crypto.PublicKey import RSA

from directorofme.authorization import groups as groups_module, requires

from flask_restful import abort
from sqlalchemy import and_

from . import api, schemas
from .. import models, db, spec
from directorofme.flask.api import dump_with_schema, load_with_schema, with_pagination_params, first_or_abort,\
                                   load_query_params, Resource

@spec.register_resource
@api.resource("/apps/<string:slug>", endpoint="apps_api")
class App(Resource):
    """
    An endpoint for retrieving and manipulating applications
    """
    @classmethod
    def validate(cls, data):
        """validate and transform a request to a `generic_(update|insert)`able dict."""
        data = copy.deepcopy(data)
        if "requested_scopes" in data:
            requested_scopes = [ groups_module.Group(display_name=s, type=groups_module.GroupTypes.scope).name
                                     for s in data.pop("requested_scopes") ]
            data["requested_access_groups"] = models.Group.query.filter(and_(
                models.Group.name.in_(requested_scopes),
                models.Group.type == groups_module.GroupTypes.scope
            )).all()

            if len(requested_scopes) != len(data["requested_access_groups"]):
                missing = set(requested_scopes) - set(r.display_name for r in data["requested_access_groups"])
                abort(409, message="No such scope{s}: {sc}".format(sc=missing, s="" if len(missing) == 1 else "s"))

        if data.get("config_schema") is not None:
            try:
                jsonschema.Draft4Validator.check_schema(data["config_schema"])
            except jsonschema.exceptions.SchemaError as e:
                abort(400, message=str(e))

        if data.get("public_key"):
            try:
                RSA.importKey(data["public_key"])
            except ValueError:
                abort(400, message="public_key must be a `pem` format RSA public key")

        return data

    @dump_with_schema(schemas.AppSchema)
    def get(self, slug):
        """
        ---
        description: Retrieve an App by slug.
        parameters:
            - api_version
            - slug
        responses:
            200:
                description: Successfully retrieve an App
                schema: AppSchema
            404:
                description: Could not find an App with current access level.
                schema: ErrorSchema
        """
        return first_or_abort(models.App.query.filter(models.App.slug == slug))

    @load_with_schema(schemas.AppSchema)
    @dump_with_schema(schemas.AppSchema)
    def put(self, app_data, slug):
        """
        ---
        description: Update an App in it's entirety.
        parameters:
            - api_version
            - slug
            - name: app
              in: body
              schema: AppSchema
        responses:
            200:
                description: Successfully updated App.
                schema: AppSchema
            301:
                description: Successfully updated App, and Slug changed.
                schema: AppSchema
            400:
                description: Invalid data sent in post data. Could be a missing
                             required field, and invalid public_key, requested
                             access or an invalid config schema.
                schema: ErrorSchema
            403:
                description: No write perissions for this object.
                schema: ErrorSchema
            404:
                description: Cannot find the requested App.
                schema: ErrorSchema
            409:
                description: Requested a scope that does not exist
                schema: ErrorSchema
        """
        return self.generic_update(db, api, models.App, "slug", slug, app_data, processor=self.validate)

    @load_with_schema(schemas.AppSchema, partial=True)
    @dump_with_schema(schemas.AppSchema)
    def patch(self, app_data, slug):
        """
        ---
        description: Apply a partial update to an App.
        parameters:
            - api_version
            - slug
            - name: app
              in: body
              schema: AppSchema
        responses:
            200:
                description: Successfully updated App.
                schema: AppSchema
            301:
                description: Successfully updated App, and Slug changed.
                schema: AppSchema
            400:
                description: Invalid data sent in put data. Could be a missing
                             required field, and invalid public_key, requested
                             access or an invalid config schema.
                schema: ErrorSchema
            403:
                description: No write perissions for this object.
                schema: ErrorSchema
            404:
                description: Cannot find the requested App.
                schema: ErrorSchema
            409:
                description: Requested a scope that does not exist
                schema: ErrorSchema
        """
        return self.generic_update(db, api, models.App, "slug", slug, app_data, processor=self.validate)


@spec.register_resource
@api.resource("/apps/", endpoint="apps_collection_api")
class Apps(Resource):
    ### TODO: Search
    @dump_with_schema(schemas.AppCollectionSchema)
    @with_pagination_params()
    def get(self, page=1, results_per_page=50):
        """
        ---
        description: Get a colleciton of Apps.
        parameters:
            - api_version
            - page
            - results_per_page
        responses:
            200:
                description: Successfully retrieve a collection of App objects.
                schema: AppCollectionSchema
            400:
                description: An invalid value was sent for a parameter.
                schema: ErrorSchema
        """
        return self.paged(models.App.query, page, results_per_page, models.App.name)

    @load_with_schema(schemas.AppSchema)
    @dump_with_schema(schemas.AppSchema)
    def post(self):
        """
        ---
        description: Apply a partial update to an App.
        parameters:
            - api_version
            - slug
            - name: app
              in: body
              schema: AppSchema
        responses:
            201:
                description: Successfully updated App.
                headers:
                    Location:
                        description: URL for the newly created App.
                        type: string
                        format: url
                schema: AppSchema
            400:
                description: Invalid data sent in post data. Could be a missing
                             required field, and invalid public_key, requested
                             access or an invalid config schema.
                schema: ErrorSchema
            403:
                description: No write permissions for this object.
                schema: ErrorSchema
            404:
                description: Cannot find the requested App.
                schema: ErrorSchema
            409:
                description: Requested a scope that does not exist
                schema: ErrorSchema
        """
        app_data = App.validate(app_data)
        return self.generic_insert(db, api, models.App, "name", app_data["name"], app_data, url_cls=App)


@spec.register_resource
@api.resource("/apps/<string:slug>/publish/<string:group_name>", endpoint="apps_publish_api")
class PublishApp(Resource):
    def post(self, slug, group_name):
        """
        ---
        description: Publish this app to a group.
        parameters:
            - api_version
            - slug
            - name: group_name
              in: path
              description: name of the group to publish to.
        responses:
            204:
                description: Successfully published.
            403:
                description: Cannot modify the publish permisisons for this App.
                schema: ErrorSchema
            404:
                description: No group or app for the passed `group_name` or `slug`.
                schema: ErrorSchema
        """
        app = first_or_abort(models.App.query.filter(models.App.slug == slug))
        group = first_or_abort(models.Group.query.filter(models.Group.name == group_name))
        app.read = app.read[:App.read.max_permissions] + (group.name,)

        db.session.add(app)
        db.session.commit()

        return None, 204

    def delete(self, slug, group_name):
        """
        ---
        description: UnPublish this app from a group.
        parameters:
            - api_version
            - slug
            - name: group_name
              in: path
              description: name of the group to publish to.
        responses:
            204:
                description: Successfully unpublished.
            403:
                description: Cannot modify the publish permisisons for this App.
                schema: ErrorSchema
            404:
                description: No group or app for the passed `group_name` or `slug`.
                schema: ErrorSchema
        """
        app = first_or_abort(models.App.query.filter(models.App.slug == slug))
        group = first_or_abort(models.Group.query.filter(models.Group.name == group_name))
        app.read = tuple(set(app.read) - set(group.name))

        db.session.add(app)
        db.session.commit()

        return None, 204
