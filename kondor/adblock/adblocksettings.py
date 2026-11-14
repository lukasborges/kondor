from PySide6.QtCore import QDateTime, SignalInstance

from kondor.core.settings.settings import Settings

ENABLED = "adBlockEnabled"
ALLOW_LIST = "adBlockAllowList"
LAST_UPDATE = "adBlockLastUpdate"


def is_enabled() -> bool:
    return bool(Settings.instance().property(ENABLED))


def set_enabled(enabled: bool) -> None:
    Settings.instance().setProperty(ENABLED, enabled)


def allow_list() -> list[str]:
    return list(Settings.instance().property(ALLOW_LIST) or [])


def set_allow_list(hosts: list[str]) -> None:
    Settings.instance().setProperty(ALLOW_LIST, hosts)


def last_update() -> QDateTime:
    value = Settings.instance().property(LAST_UPDATE)
    return value if isinstance(value, QDateTime) else QDateTime()


def set_last_update(time: QDateTime) -> None:
    Settings.instance().setProperty(LAST_UPDATE, time)


def changed_signal(name: str) -> SignalInstance:
    signal: SignalInstance = getattr(Settings.instance(), f"{name}Changed")
    return signal
