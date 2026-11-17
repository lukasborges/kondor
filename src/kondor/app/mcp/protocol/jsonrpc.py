import json
from typing import Any

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602

JsonObject = dict[str, Any]


class InvalidParamsError(Exception):
    pass


def parse_line(line: bytes) -> JsonObject | None:
    try:
        message = json.loads(line)
    except ValueError:
        return None
    return message if isinstance(message, dict) else None


def success(request_id: object, result: JsonObject) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def failure(request_id: object, code: int, message: str) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def encode_line(message: JsonObject) -> bytes:
    return json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n"
