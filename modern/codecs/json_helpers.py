import json

from .types import JsonValue


def std_dump(value: JsonValue) -> bytes:
    return json.dumps(value).encode()


std_load = json.loads


try:
    import orjson
except ImportError:  # pragma: no cover
    pass
else:
    orjson_dump = orjson.dumps
    orjson_load = orjson.loads


try:
    import ujson
except ImportError:  # pragma: no cover
    pass
else:

    def ujson_dump(value: JsonValue) -> bytes:
        return ujson.dumps(value).encode()

    ujson_load = ujson.loads


try:
    import simplejson
except ImportError:  # pragma: no cover
    pass
else:

    def simplejson_dump(value: JsonValue) -> bytes:
        return simplejson.dumps(value).encode()

    simplejson_load = simplejson.loads
