import copy
import jsonschema

from directorofme.authorization import groups as groups_module, requires

from flask_restful import abort
from sqlalchemy import and_

from . import api, schemas
from .. import models, db, spec
from directorofme.flask.api import dump_with_schema, load_with_schema, with_pagination_params, first_or_abort,\
                                   load_query_params, Resource, uuid_or_abort

@spec.register_resource
@api.resource("/apps/<string:slug>", endpoint="apps_api")
class App(Resource):
    """
    An endpoint for retrieving and manipulating applications
    """
    @classmethod
    def validate(cls, data, _=None):
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
                models.App.make_cipher(public_key=data.get("public_key"))
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

    def delete(self, slug):
        """
        ---
        description: Delete an App.
        parameters:
            - api_version
            - slug
        responses:
            204:
                description: App deleted.
            403:
                description: No permission to delete this App object.
                schema: ErrorSchema
            404:
                description: Could not find existing App for slug.
                schema: ErrorSchema
        """
        return self.generic_delete(db, models.App, "slug", slug)


@spec.register_resource
@api.resource("/apps/<string:slug>/encrypt", endpoint="apps_api:encrypt")
class AppEncrypt(Resource):
    @load_with_schema(schemas.AppEncryptSchema)
    @dump_with_schema(schemas.AppEncryptSchema)
    def post(self, encrypt_obj, slug):
        """
        ---
        description: Encrypt a payload using an App's public key
        parameters:
            - api_version
            - slug
            - in: body
              schema: AppEncryptSchema
              name: encrypt
              description: Payload to encrypt
        responses:
            200:
                description: Successfully encrypted the payload.
                schema: AppEncryptSchema
            400:
                description: An invalid value was sent for a parameter.
                schema: ErrorSchema
            404:
                description: Could not find App associated with `slug`.
                schema: ErrorSchema
        """
        if encrypt_obj["encryption"] != "RSA":
            abort(400, message="Encryption must be one of: (`RSA`); not {}".format(encrypt_obj["encryption"]))

        app = first_or_abort(models.App.query.filter(models.App.slug == slug))
        try:
            return {
                "value": app.encrypt(encrypt_obj["value"]),
                "slug": app.slug
            }
        except ValueError as e:
            abort(400, message=str(e))


@spec.register_resource
@api.resource("/apps/<string:slug>/decrypt", endpoint="apps_api:decrypt")
class AppDecrypt(Resource):
    @load_with_schema(schemas.AppDecryptSchema)
    @dump_with_schema(schemas.AppDecryptSchema)
    def post(self, decrypt_obj, slug):
        """
        ---
        description: Decrypt a payload using the private_key associated with an App.
        parameters:
            - api_version
            - slug
            - in: body
              schema: AppDecryptSchema
              name: decrypt
              description: Payload to decrypt and private key to decrypt it with.
        responses:
            200:
                description: Successfully decrypted the payload.
                schema: AppDecryptSchema
            400:
                description: An invalid value was sent for a parameter.
                schema: ErrorSchema
            404:
                description: Could not find App associated with `slug`.
                schema: ErrorSchema
        """
        if decrypt_obj["encryption"] != "RSA":
            abort(400, message="Encryption must be one of: (`RSA`); not {}".format(decrypt_obj["encryption"]))

        app = first_or_abort(models.App.query.filter(models.App.slug == slug))
        try:
            return {
                "value": app.decrypt(decrypt_obj["private_key"], decrypt_obj["value"]),
                "slug": app.slug
            }
        except ValueError as e:
            abort(400, message=str(e))


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
    def post(self, app_data):
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
            409:
                description: Requested a scope that does not exist
                schema: ErrorSchema
        """
        return self.generic_insert(db, api, models.App, App.validate(app_data), "slug", url_cls=App)


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
        app.read = app.read[:models.App.read.max_permissions] + (group.name,)

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
        app.read = tuple(set(app.read) - set([group.name]))

        db.session.add(app)
        db.session.commit()

        return None, 204

@spec.register_resource
@api.resource("/installed_apps/<string:id>", endpoint="installed_apps_api")
class InstalledApp(Resource):
    @classmethod
    def validate(cls, data, id=None):
        """scopes and jsonschema validation extras"""
        data = copy.deepcopy(data)
        app_slug = data.pop("app_slug", None)
        if app_slug is None:
            data["app"] = first_or_abort(models.InstalledApp.query.filter(
                models.InstalledApp.id == data.get("id", id)
            )).app
        else:
            data["app"] = first_or_abort(models.App.query.filter(models.App.slug == app_slug), 409)

        if "scopes" in data:
            scopes = [ groups_module.Group(display_name=s, type=groups_module.GroupTypes.scope).name
                                           for s in data.pop("scopes") ]

            data["access_groups"] = models.Group.query.filter(and_(
                models.Group.name.in_(scopes),
                models.Group.type == groups_module.GroupTypes.scope
            )).all()

            if len(scopes) != len(data["access_groups"]):
                missing = set(scopes) - set(r.display_name for r in data["access_groups"])
                abort(409, message="No such scope{s}: {sc}".format(sc=missing, s="" if len(missing) == 1 else "s"))

            unrequested = set([g.display_name for g in data["access_groups"]]) - \
                          set([g.display_name for g in data["app"].requested_access_groups])
            if unrequested:
                abort(400, message="Granted access to unrequested scopes: {}".format(tuple(unrequested)))

        config = data.get("config")
        if config is not None:
            if data["app"].config_schema is not None:
                try:
                    jsonschema.validate(config, data["app"].config_schema)
                except (jsonschema.exceptions.ValidationError, jsonschema.exceptions.SchemaError) as e:
                    abort(400, message=str(e))

        return data

    @dump_with_schema(schemas.InstalledAppSchema)
    def get(self, id):
        """
        ---
        description: Retrieve an InstalledApp by id.
        parameters:
            - api_version
            - id
        responses:
            200:
                description: Successfully retrieve an InstalledApp
                schema: InstalledAppSchema
            404:
                description: Could not find an InstalledApp with current access level.
                schema: ErrorSchema
        """
        return first_or_abort(models.InstalledApp.query.filter(models.InstalledApp.id == uuid_or_abort(id)))

    @load_with_schema(schemas.InstalledAppSchema)
    @dump_with_schema(schemas.InstalledAppSchema)
    def put(self, app_data, id):
        """
            ---
            description: Update an InstalledApp in it's entirety.
            parameters:
                - api_version
                - id
                - name: installed_app
                  in: body
                  schema: InstalledAppSchema
            responses:
                200:
                    description: Successfully updated InstalledApp.
                    schema: InstalledAppSchema
                400:
                    description: Invalid UUID, missing required field, or invalid config data.
                    schema: ErrorSchema
                403:
                    description: No write permissions for this object.
                    schema: ErrorSchema
                404:
                    description: Cannot find the requested InstalledApp.
                    schema: ErrorSchema
                409:
                    description: No App associated with `app_slug`..
                    schema: ErrorSchema
        """
        id = uuid_or_abort(id)
        return self.generic_update(db, api, models.InstalledApp, "id", id, app_data, processor=self.validate)

    @load_with_schema(schemas.InstalledAppSchema, partial=True)
    @dump_with_schema(schemas.InstalledAppSchema)
    def patch(self, app_data, id):
        """
            ---
            description: Partially update an InstalledApp.
            parameters:
                - api_version
                - id
                - name: installed_app
                  in: body
                  schema: InstalledAppSchema
            responses:
                200:
                    description: Successfully updated InstalledApp.
                    schema: InstalledAppSchema
                400:
                    description: Invalid UUID, missing required field, or invalid config data.
                    schema: ErrorSchema
                403:
                    description: No write permissions for this object.
                    schema: ErrorSchema
                404:
                    description: Cannot find the requested InstalledApp.
                    schema: ErrorSchema
                409:
                    description: No App associated with `app_slug`..
                    schema: ErrorSchema
        """
        id = uuid_or_abort(id)
        return self.generic_update(db, api, models.InstalledApp, "id", id, app_data, processor=self.validate)

    def delete(self, id):
        """
        ---
        description: Delete an InstalledApp.
        parameters:
            - api_version
            - id
        responses:
            204:
                description: InstalledApp deleted.
            403:
                description: No permission to delete this InstalledApp object.
                schema: ErrorSchema
            404:
                description: Could not find existing InstalledApp for slug.
                schema: ErrorSchema
        """
        return self.generic_delete(db, models.InstalledApp, "id", uuid_or_abort(id))


@spec.register_resource
@api.resource("/installed_apps/", endpoint="installed_apps_collection_api")
class InstalledApps(Resource):
    @dump_with_schema(schemas.InstalledAppCollectionSchema)
    @with_pagination_params()
    @load_query_params(schemas.InstalledAppCollectionQuerySchema)
    def get(self, page=1, results_per_page=50, app=None):
        """
        ---
        description: Get a colleciton of InstalledApps.
        parameters:
            - api_version
            - page - results_per_page
            - name: app
              in: query
              description: slug of App to filter by.
        responses:
            200:
                description: Successfully retrieve a collection of InstalledApp objects.
                schema: InstalledAppCollectionSchema
            400:
                description: An invalid value was sent for a parameter.
                schema: ErrorSchema
        """
        query = models.InstalledApp.query
        if app is not None:
            query = query.join(models.InstalledApp.app).filter(models.App.slug == app)

        return self.paged(query, page, results_per_page, models.InstalledApp.created, app=app)


    @load_with_schema(schemas.InstalledAppSchema)
    @dump_with_schema(schemas.InstalledAppSchema)
    def post(self, data):
        """
        ---
        description: Create a new InstalledApp.
        parameters:
            - api_version
            - id
            - name: installed_app
              in: body
              schema: InstalledAppSchema
        responses:
            201:
                description: Successfully updated InstalledApp.
                schema: InstalledAppSchema
                headers:
                    Location:
                        description: URL for the newly created InstalledApp.
                        type: string
                        format: url
            400:
                description: Invalid UUID, missing required field, or invalid config data.
                schema: ErrorSchema
            403:
                description: No write permissions for this object.
                schema: ErrorSchema
            409:
                description: No App associated with `app_slug`..
                schema: ErrorSchema
        """
        data = InstalledApp.validate(data)
        return self.generic_insert(db, api, models.InstalledApp, data, "id", url_cls=InstalledApp)


@spec.register_resource
@api.resource("/apps/<string:app>/install/", endpoint="apps_install_app_api")
class InstallApp(Resource):
    @load_with_schema(schemas.InstallAppSchema)
    @dump_with_schema(schemas.InstalledAppSchema)
    def post(self, data, app):
        """
        ---
        description: Create a new InstalledApp.
        parameters:
            - api_version
            - id
            - name: installed_app
              in: body
              schema: InstalledAppSchema
        responses:
            201:
                description: Successfully updated InstalledApp.
                schema: InstalledAppSchema
                headers:
                    Location:
                        description: URL for the newly created InstalledApp.
                        type: string
                        format: url
            400:
                description: Invalid UUID, missing required field, or invalid config data.
                schema: ErrorSchema
            403:
                description: No write permissions for this object.
                schema: ErrorSchema
            404:
                description: No App found for `app`.
                schema: ErrorSchema
        """
        app = first_or_abort(models.App.query.filter(models.App.slug == app))
        data["app_slug"] = app.slug
        data = InstalledApp.validate(data)
        return self.generic_insert(db, api, models.InstalledApp, data, "id", url_cls=InstalledApp)
