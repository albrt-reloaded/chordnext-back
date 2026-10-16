from marshmallow import Schema, fields, validate


class SetlistItemSchema(Schema):
    id = fields.String(load_default=None, allow_none=True)
    songId = fields.String(required=True)
    position = fields.Integer(load_default=None, allow_none=True)
    keyOverride = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=8))
    notes = fields.String(load_default="")


class SetlistSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(load_default="")
    items = fields.List(fields.Nested(SetlistItemSchema), load_default=None, allow_none=True)
    revision = fields.Integer(load_default=None, allow_none=True)


class ReorderSchema(Schema):
    songIds = fields.List(fields.String(), required=True)
