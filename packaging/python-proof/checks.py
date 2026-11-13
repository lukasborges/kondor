from PySide6.QtDBus import QDBusConnection, QDBusInterface

from results import Results

BUS_NAME = "org.freedesktop.DBus"


def check_dbus() -> str | None:
    bus = QDBusConnection.sessionBus()
    interface = QDBusInterface(BUS_NAME, "/org/freedesktop/DBus", BUS_NAME, bus)
    arguments = interface.call("ListNames").arguments()
    names = arguments[0] if arguments else []
    return None if BUS_NAME in names else f"{BUS_NAME} not in ListNames reply"


def style_failure(passed: bool, reason: str, warnings: list[str]) -> str | None:
    if warnings:
        return "QML warnings: " + "; ".join(warnings)
    return None if passed else reason


def module_failure(passed: bool, same_instance: bool) -> str | None:
    if not same_instance:
        return "engine.singletonInstance is not ProofState.instance()"
    return None if passed else "Proof.qml did not reach ProofState"


def record_dbus(results: Results) -> None:
    results.record("dbus", check_dbus())
