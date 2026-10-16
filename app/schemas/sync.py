from marshmallow import Schema, fields


class SyncPushSchema(Schema):
    """Payload de push off-line-first.

    Cada colección contiene registros completos con `id`, `updatedAt`,
    `revision` y `deleted` para resolver conflictos last-write-wins.
    """

    deviceId = fields.String(load_default=None, allow_none=True)
    songs = fields.List(fields.Dict(), load_default=list)
    setlists = fields.List(fields.Dict(), load_default=list)
    tags = fields.List(fields.Dict(), load_default=list)
    progressions = fields.List(fields.Dict(), load_default=list)
