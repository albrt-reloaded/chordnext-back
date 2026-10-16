from marshmallow import Schema, fields, validate


class CommaSeparatedList(fields.Field):
    """Acepta una lista JSON o un string tipo query param "a,b,c"."""

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None or value == "":
            return None
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [part.strip() for part in str(value).split(",") if part.strip()]


class SongSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    artist = fields.String(load_default="", validate=validate.Length(max=255))
    key = fields.String(load_default="C", validate=validate.Length(max=8))
    capo = fields.Integer(load_default=0, validate=validate.Range(min=0, max=12))
    bpm = fields.Integer(load_default=90, validate=validate.Range(min=20, max=400))
    timeSignature = fields.String(load_default="4/4", validate=validate.Length(max=8))
    content = fields.String(load_default="")
    contentJson = fields.Dict(load_default=None, allow_none=True)
    hasChords = fields.Boolean(load_default=True)
    notes = fields.String(load_default="")
    # tags: lista de IDs existentes o nombres nuevos
    tagIds = fields.List(fields.String(), load_default=list)
    tagNames = fields.List(fields.String(), load_default=list)
    revision = fields.Integer(load_default=None, allow_none=True)


class SongSearchSchema(Schema):
    q = fields.String(load_default="")
    key = fields.String(load_default=None, allow_none=True)
    artist = fields.String(load_default=None, allow_none=True)
    tags = CommaSeparatedList(load_default=None, allow_none=True)
    bpmMin = fields.Integer(load_default=None, allow_none=True)
    bpmMax = fields.Integer(load_default=None, allow_none=True)
    hasChords = fields.Boolean(load_default=None, allow_none=True)
    sort = fields.String(load_default="updatedAt", validate=validate.OneOf(
        ["updatedAt", "title", "artist", "bpm", "createdAt"]
    ))
    order = fields.String(load_default="desc", validate=validate.OneOf(["asc", "desc"]))
    limit = fields.Integer(load_default=50, validate=validate.Range(min=1, max=200))
    offset = fields.Integer(load_default=0, validate=validate.Range(min=0))
