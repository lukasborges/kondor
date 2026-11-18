import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClientIdentity:
    name: str
    version: str


@dataclass(frozen=True)
class RemoteControlState:
    is_active: bool
    port: int


POINTER_KINDS = ("move", "press")


@dataclass(frozen=True)
class PointerAction:
    target_id: str
    kind: str
    x: float
    y: float


def hello_line(client: ClientIdentity) -> bytes:
    return encode({"session": "hello", "clientName": client.name, "clientVersion": client.version})


def ports_line(ports: list[int]) -> bytes:
    return encode({"session": "ports", "ports": ports})


def pointer_line(target_id: str, kind: str, point: tuple[float, float]) -> bytes:
    return encode(
        {"session": "pointer", "target": target_id, "kind": kind, "x": point[0], "y": point[1]}
    )


def own_line(target_id: str) -> bytes:
    return encode({"session": "own", "target": target_id})


def agent_tabs_query_line() -> bytes:
    return encode({"session": "agent-tabs?"})


def agent_tabs_line(target_ids: list[str]) -> bytes:
    return encode({"agent-tabs": target_ids})


def agent_tab_change_line(target_id: str, has_access: bool) -> bytes:
    return encode({"agent-tab": target_id, "access": has_access})


def reply_line(state: RemoteControlState) -> bytes:
    return encode({"active": state.is_active, "port": state.port})


def encode(message: dict[str, Any]) -> bytes:
    return json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n"


def parse_object(line: bytes) -> dict[str, Any] | None:
    try:
        parsed = json.loads(line)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def is_session_line(line: bytes) -> bool:
    parsed = parse_object(line)
    return parsed is not None and "session" in parsed


def parse_client(parsed: dict[str, Any]) -> ClientIdentity:
    return ClientIdentity(str(parsed.get("clientName", "")), str(parsed.get("clientVersion", "")))


def parse_ports(parsed: dict[str, Any]) -> list[int]:
    ports = parsed.get("ports")
    return [port for port in ports if isinstance(port, int)] if isinstance(ports, list) else []


def parse_reply(line: bytes) -> RemoteControlState | None:
    parsed = parse_object(line)
    if parsed is None or "active" not in parsed:
        return None
    return RemoteControlState(parsed["active"] is True, int(parsed.get("port", 0)))


def parse_pointer(parsed: dict[str, Any]) -> PointerAction | None:
    target_id, kind = parsed.get("target"), parsed.get("kind")
    x, y = number_or_none(parsed.get("x")), number_or_none(parsed.get("y"))
    if not isinstance(target_id, str) or kind not in POINTER_KINDS:
        return None
    if x is None or y is None:
        return None
    return PointerAction(target_id, str(kind), x, y)


def number_or_none(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def parse_target(parsed: dict[str, Any]) -> str:
    target_id = parsed.get("target")
    return target_id if isinstance(target_id, str) else ""


def parse_agent_tabs(line: bytes) -> list[str] | None:
    parsed = parse_object(line)
    ids = parsed.get("agent-tabs") if parsed is not None else None
    if not isinstance(ids, list):
        return None
    return [target_id for target_id in ids if isinstance(target_id, str)]


def parse_agent_tab_change(line: bytes) -> tuple[str, bool] | None:
    parsed = parse_object(line)
    if parsed is None or not isinstance(parsed.get("agent-tab"), str):
        return None
    return parsed["agent-tab"], parsed.get("access") is True
