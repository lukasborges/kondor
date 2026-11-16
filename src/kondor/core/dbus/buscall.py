from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from jeepney import HeaderFields, MessageType


@dataclass(frozen=True)
class BusCall:
    path: str
    interface: str
    member: str
    body: tuple[Any, ...]


@dataclass(frozen=True)
class BusReply:
    signature: str = ""
    body: tuple[Any, ...] = ()


@dataclass(frozen=True)
class BusError:
    name: str


@dataclass(frozen=True)
class BusSignal:
    path: str
    interface: str
    member: str
    signature: str = ""
    body: tuple[Any, ...] = ()


CallHandler = Callable[[BusCall], BusReply | BusError | None]


def is_method_call(message: Any) -> bool:
    return bool(message.header.message_type == MessageType.method_call)


def call_from_message(message: Any) -> BusCall:
    fields = message.header.fields
    return BusCall(
        path=fields.get(HeaderFields.path, ""),
        interface=fields.get(HeaderFields.interface, ""),
        member=fields.get(HeaderFields.member, ""),
        body=tuple(message.body),
    )
