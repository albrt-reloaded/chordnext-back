from marshmallow import Schema, fields, validate


class TagSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=64))
    color = fields.String(load_default="#6366f1", validate=validate.Length(max=16))
    revision = fields.Integer(load_default=None, allow_none=True)
