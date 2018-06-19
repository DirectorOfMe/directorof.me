from marshmallow import fields, Schema

__all__ = [ "Event", "InstalledAppRequest", "InstalledApp" ]

class Event(Schema):
    id = fields.UUID(required=True)
    created = fields.DateTime(required=True)
    updated = fields.DateTime(required=True)

    event_time = fields.DateTime(required=True)

    event_type_slug = fields.String(required=True)
    data = fields.Dict(required=True)

class InstalledAppRequest(Schema):
    app_slug = fields.String(required=True)
    config = fields.Dict(allow_none=True)
    scopes = fields.List(fields.String())

class InstalledApp(InstalledAppRequest):
    id = fields.UUID(required=True)
    created = fields.DateTime()
    updated = fields.DateTime()

    _links = fields.Dict(keys=fields.String(), values=fields.Url())
