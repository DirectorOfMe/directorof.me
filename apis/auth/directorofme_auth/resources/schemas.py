from marshmallow_enum import EnumField
from directorofme.authorization import groups
from .. import spec, marshmallow

### Session Structures (authentication)
@spec.register_schema("SessionQuerySchema")
class SessionQuerySchema(marshmallow.Schema):
    installed_app_id = marshmallow.UUID()
    state = marshmallow.UUID()


class SessionAppSchema(marshmallow.Schema):
    id = marshmallow.UUID(required=True)
    app_id = marshmallow.UUID(required=True)
    app_name = marshmallow.String(required=True)
    config = marshmallow.Dict(allow_none=True, required=False)


class SessionProfileSchema(marshmallow.Schema):
    id = marshmallow.UUID(required=True)
    email = marshmallow.Email(required=True)


class SessionGroupSchema(marshmallow.Schema):
    name = marshmallow.String(required=True)
    display_name = marshmallow.String(required=True)
    type = EnumField(groups.GroupTypes, required=True)


@spec.register_schema("SessionSchema")
class SessionSchema(marshmallow.Schema):
    app = marshmallow.Nested(SessionAppSchema, allow_none=True)
    profile = marshmallow.Nested(SessionProfileSchema)
    groups = marshmallow.Nested(SessionGroupSchema, many=True)
    environment = marshmallow.Dict()
    default_object_perms = marshmallow.Dict(marshmallow.Nested(SessionGroupSchema, many=True))

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.session_api")
    })

### Group
@spec.register_schema("GroupSchema")
class GroupSchema(marshmallow.Schema):
    display_name = marshmallow.String(required=True)
    type = EnumField(groups.GroupTypes, required=True)

    scope_name = marshmallow.String(allow_none=True)
    scope_permission = marshmallow.String(allow_none=True)

    id = marshmallow.UUID(required=True, dump_only=True)
    name = marshmallow.String(required=True, dump_only=True)
    created = marshmallow.DateTime(dump_only=True)
    updated = marshmallow.DateTime(dump_only=True)

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.groups_api", name="<name>"),
        "collection": marshmallow.URLFor("auth.groups_collection_api"),
        "members": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="members"),
        "member_of": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="member_of"),
    }, dump_only=True)


@spec.register_schema("GroupCollectionQuerySchema")
class GroupCollectionQuerySchema(marshmallow.Schema):
    type = EnumField(groups.GroupTypes, allow_none=True)
    scope_name = marshmallow.String(allow_none=True)


@spec.register_schema("GroupCollectionSchema")
class GroupCollectionSchema(spec.paginated_collection_schema(GroupSchema, "auth.groups_collection_api",
                                                             type="<type>", scope_name="<scope_name>")
):
    pass

@spec.register_schema("GroupMembersSchema")
class GroupMembersSchema(marshmallow.Schema):
    collection = marshmallow.Nested(GroupSchema, many=True, required=True, attribute="members")

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="members"),
        "member_of": marshmallow.URLFor("auth.groups_api", name="<name>"),
    }, dump_only=True)

@spec.register_schema("GroupMembersSchema")
class GroupMemberOfSchema(marshmallow.Schema):
    collection = marshmallow.Nested(GroupSchema, many=True, required=True,
                                    attribute="member_of")
    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="member_of"),
        "member": marshmallow.URLFor("auth.groups_api", name="<name>"),
    }, dupm_only=True)


### Profile
@spec.register_schema("ProfileSchema")
class ProfileSchema(SessionProfileSchema):
    preferences = marshmallow.Dict(allow_none=True)

    created = marshmallow.DateTime(dump_only=True)
    updated = marshmallow.DateTime(dump_only=True)

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.profiles_api", email="<email>"),
        "collection": marshmallow.URLFor("auth.profiles_collection_api"),
        "group_of_one": marshmallow.URLFor("auth.profiles_api.group_of_one", email="<email>"),
        "licenses": marshmallow.URLFor("auth.profiles_api.licenses", email="<email>"),
    }, dump_only=True)

@spec.register_schema("ProfileCollectionSchema")
class ProfileCollectionSchema(
    spec.paginated_collection_schema(ProfileSchema, "auth.profiles_collection_api")
):
    pass

### License
@spec.register_schema("LicenseSchema")
class LicenseSchema(marshmallow.Schema):
    seats = marshmallow.Integer(required=True)
    notes = marshmallow.String(default="")

    created = marshmallow.DateTime(dump_only=True)
    updated = marshmallow.DateTime(dump_only=True)

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.license_api", id="<id>"),
        "collection": marshmallow.URLFor("auth.licenses_collection_api"),
        "managing_group": marshmallow.URLFor("auth.licenses_api.managing_group", id="<id>"),
        "groups": marshmallow.URLFor("auth.licenses_api.groups", id="<id>"),
        "profiles": marshmallow.URLFor("auth.licenses_api.profiles", id="<id>")
    }, dump_only=True)

@spec.register_schema("GroupsByLicenseSchema")
class LicenseGroups(
    spec.paginated_collection_schema(LicenseSchema, "auth.licenses_api:groups", id="<id>")
):
    pass

@spec.register_schema("ProfilesByLicenseSchema")
class LicenseProfiles(
    spec.paginated_collection_schema(ProfileSchema, "auth.licenses_api:profiles", id="<id>")
):
    pass

@spec.register_schema("ProfileCollectionSchema")
class ProfileLicenses(
    spec.paginated_collection_schema(LicenseSchema, "auth.profiles_api:licenses", email="<email>")
):
    pass

### App
@spec.register_schema("AppSchema")
class AppSchema(marshmallow.Schema):
    name = marshmallow.String(required=True)
    desc = marshmallow.String(required=True)
    url = marshmallow.Url(required=True)

    callback_url = marshmallow.Url(allow_none=True)
    config_schema = marshmallow.Dict(allow_none=True)
    public_key = marshmallow.String(allow_none=True)
    requested_scopes = marshmallow.List(marshmallow.String, required=True)

    slug = marshmallow.String(required=True, dump_only=True)
    created = marshmallow.DateTime(dump_only=True)
    updated = marshmallow.DateTime(dump_only=True)
    requested_scopes = marshmallow.Method(serialize="dump_scopes", deserialize="load_scopes", required=True)

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.apps_api", slug="<slug>"),
        "collection": marshmallow.URLFor("auth.apps_collection_api"),
        "publish": marshmallow.URLFor("auth.apps_publish_api", slug="<slug>", group_name="f-user")
    }, dump_only=True)

    def load_scopes(self, value):
        return marshmallow.List(marshmallow.String)._deserialize(value, None, None)

    def dump_scopes(self, obj):
        return marshmallow.List(marshmallow.String)._serialize([
            g.display_name for g in obj.requested_access_groups
        ], None, None)

@spec.register_schema("AppCollectionSchema")
class AppCollectionSchema(spec.paginated_collection_schema(AppSchema, "auth.apps_collection_api")):
    pass
