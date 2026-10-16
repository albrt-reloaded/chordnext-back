from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=128))
    name = fields.String(load_default="", validate=validate.Length(max=120))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class GoogleAuthSchema(Schema):
    idToken = fields.String(required=True)
    name = fields.String(load_default=None, allow_none=True)
    avatarUrl = fields.String(load_default=None, allow_none=True)


class UpdateProfileSchema(Schema):
    name = fields.String(validate=validate.Length(max=120))
    avatarUrl = fields.String(allow_none=True)
    preferredKey = fields.String(validate=validate.Length(max=8))
    theme = fields.String(validate=validate.OneOf(["system", "light", "dark"]))
    fontSize = fields.Integer(validate=validate.Range(min=10, max=48))
