from marshmallow import Schema, fields, validate


class ProgressionSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    degrees = fields.String(required=True, validate=validate.Length(min=1, max=255))
    key = fields.String(load_default="C", validate=validate.Length(max=8))
    preferred = fields.Boolean(load_default=False)
    revision = fields.Integer(load_default=None, allow_none=True)
