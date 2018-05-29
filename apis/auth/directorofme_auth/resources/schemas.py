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


@spec.register_schema("SessionReponseSchema")
class SessionResponseSchema(marshmallow.Schema):
    app = marshmallow.Nested(SessionAppSchema, allow_none=True)
    profile = marshmallow.Nested(SessionProfileSchema)
    groups = marshmallow.Nested(SessionGroupSchema, many=True)
    environment = marshmallow.Dict()
    default_object_perms = marshmallow.Dict(marshmallow.Nested(SessionGroupSchema, many=True))

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.session_api")
    })

### Group
@spec.register_schema("GroupRequestSchema")
class GroupRequestSchema(marshmallow.Schema):
    display_name = marshmallow.String(required=True)
    type = EnumField(groups.GroupTypes, required=True)

    scope_name = marshmallow.String(allow_none=True)
    scope_permission = marshmallow.String(allow_none=True)


@spec.register_schema("GroupResponseSchema")
class GroupResponseSchema(GroupRequestSchema):
    id = marshmallow.UUID(required=True)
    name = marshmallow.String(required=True)
    created = marshmallow.DateTime()
    updated = marshmallow.DateTime()

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.groups_api", name="<name>"),
        "collection": marshmallow.URLFor("auth.groups_collection_api"),
        "members": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="members"),
        "member_of": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="member_of"),
    })


class GroupCollectionQuerySchema(marshmallow.Schema):
    type = EnumField(groups.GroupTypes, allow_none=True)
    scope_name = marshmallow.String(allow_none=True)


@spec.register_schema("GroupCollectionSchema")
class GroupCollectionSchema(spec.paginated_collection_schema(GroupResponseSchema, "auth.groups_collection_api",
                                                             type="<type>", scope_name="<scope_name>")
):
    pass

@spec.register_schema("GroupMembersRequestSchema")
class GroupMembersRequestSchema(marshmallow.Schema):
    collection = marshmallow.Nested(GroupRequestSchema, many=True, required=True)


@spec.register_schema("GroupMembersResponseSchema")
class GroupMembersResponseSchema(marshmallow.Schema):
    collection = marshmallow.Nested(GroupResponseSchema, many=True, required=True,
                                    attribute="members")
    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="members"),
        "member_of": marshmallow.URLFor("auth.groups_api", name="<name>"),
    })

@spec.register_schema("GroupMembersResponseSchema")
class GroupMemberOfResponseSchema(marshmallow.Schema):
    collection = marshmallow.Nested(GroupResponseSchema, many=True, required=True,
                                    attribute="member_of")
    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.groups_api:list", name="<name>", list_name="member_of"),
        "member": marshmallow.URLFor("auth.groups_api", name="<name>"),
    })


### Profile
@spec.register_schema("ProfileRequestSchema")
class ProfileRequestSchema(SessionProfileSchema):
    preferences = marshmallow.Dict(allow_none=True)


@spec.register_schema("ProfileResponseSchema")
class ProfileResponseSchema(ProfileRequestSchema):
    created = marshmallow.DateTime()
    updated = marshmallow.DateTime()

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.profiles_api", email="<email>"),
        "collection": marshmallow.URLFor("auth.profiles_collection_api"),
        "group_of_one": marshmallow.URLFor("auth.profiles_api.group_of_one", email="<email>"),
        "licenses": marshmallow.URLFor("auth.profiles_api.licenses", email="<email>"),
    })

@spec.register_schema("ProfileCollectionSchema")
class ProfileCollectionSchema(
    spec.paginated_collection_schema(ProfileResponseSchema, "auth.profiles_collection_api")
):
    pass

### License
@spec.register_schema("LicenseRequestSchema")
class LicenseRequestSchema(marshmallow.Schema):
    seats = marshmallow.Integer(required=True)
    notes = marshmallow.String(default="")


@spec.register_schema("LicenseResponseSchema")
class LicenseResponseSchema(LicenseRequestSchema):
    created = marshmallow.DateTime()
    updated = marshmallow.DateTime()

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.license_api", id="<id>"),
        "collection": marshmallow.URLFor("auth.licenses_collection_api"),
        "managing_group": marshmallow.URLFor("auth.licenses_api.managing_group", id="<id>"),
        "groups": marshmallow.URLFor("auth.licenses_api.groups", id="<id>"),
        "profiles": marshmallow.URLFor("auth.licenses_api.profiles", id="<id>")
    })

@spec.register_schema("GroupsByLicenseSchema")
class LicenseGroups(
    spec.paginated_collection_schema(GroupResponseSchema, "auth.licenses_api:groups", id="<id>")
):
    pass

@spec.register_schema("ProfilesByLicenseSchema")
class LicenseProfiles(
    spec.paginated_collection_schema(ProfileResponseSchema, "auth.licenses_api:profiles", id="<id>")
):
    pass

@spec.register_schema("ProfileCollectionSchema")
class ProfileLicenses(
    spec.paginated_collection_schema(LicenseResponseSchema, "auth.profiles_api:licenses", email="<email>")
):
    pass

### App
@spec.register_schema("AppRequestSchema")
class AppRequestSchema(marshmallow.Schema):
    name = marshmallow.String(required=True)
    desc = marshmallow.String(required=True)
    url = marshmallow.Url(required=True)

    callback_url = marshmallow.Url(allow_none=True)
    config_schema = marshmallow.Dict(allow_none=True)
    public_key = marshmallow.String(allow_none=True)
    requested_scopes = marshmallow.List(marshmallow.String, required=True)


@spec.register_schema("AppRequestSchema")
class AppResponseSchema(marshmallow.Schema):
    slug = marshmallow.String(required=True)
    created = marshmallow.DateTime()
    updated = marshmallow.DateTime()

    _links = marshmallow.Hyperlinks({
        "self": marshmallow.URLFor("auth.apps_api"),
        "collection": marshmallow.URLFor("auth.apps_collection_api"),
        "publish": marshmallow.URLFor("/apps/<slug>/publish/f-users")
    })

@spec.register_schema("AppCollectionSchema")
class AppCollectionSchema(spec.paginated_collection_schema(AppResponseSchema, "auth.apps_collection_api")):
    pass
