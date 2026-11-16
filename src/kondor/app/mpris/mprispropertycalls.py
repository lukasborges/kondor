from kondor.app.mpris.mprisproperties import Properties
from kondor.core.dbus.buscall import BusCall, BusError, BusReply

UNKNOWN_PROPERTY = "org.freedesktop.DBus.Error.UnknownProperty"
READ_ONLY = "org.freedesktop.DBus.Error.PropertyReadOnly"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"


def get_property(
    interfaces: dict[str, Properties], interface: str, name: str
) -> BusReply | BusError:
    value = interfaces.get(interface, {}).get(name)
    if value is None:
        return BusError(UNKNOWN_PROPERTY)
    return BusReply("v", (value,))


def get_all_properties(interfaces: dict[str, Properties], interface: str) -> BusReply:
    return BusReply("a{sv}", (interfaces.get(interface, {}),))


def property_call(interfaces: dict[str, Properties], call: BusCall) -> BusReply | BusError | None:
    if call.member == "Get":
        return get_property(interfaces, *call.body)
    if call.member == "GetAll":
        return get_all_properties(interfaces, *call.body)
    return BusError(READ_ONLY) if call.member == "Set" else None
