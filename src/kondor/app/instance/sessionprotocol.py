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


def hello_line(client: ClientIdentity) -> bytes:
    return encode({"session": "hello", "clientName": client.name, "clientVersion": client.version})


def ports_line(ports: list[int]) -> bytes:
    return encode({"session": "ports", "ports": ports})


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
