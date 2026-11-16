from collections.abc import Mapping, MutableMapping

PLATFORM_VARIABLE = "QT_QPA_PLATFORM"
AFFECTED_QT_SERIES = "6.11."


def is_wayland_session(environment: Mapping[str, str]) -> bool:
    return "WAYLAND_DISPLAY" in environment or environment.get("XDG_SESSION_TYPE") == "wayland"


def is_x_server_reachable(environment: Mapping[str, str]) -> bool:
    return "DISPLAY" in environment


def should_use_xwayland(environment: Mapping[str, str], qt_version: str) -> bool:
    return (
        PLATFORM_VARIABLE not in environment
        and qt_version.startswith(AFFECTED_QT_SERIES)
        and is_wayland_session(environment)
        and is_x_server_reachable(environment)
    )


def use_xwayland_when_qt_breaks_wayland_popups(
    environment: MutableMapping[str, str], qt_version: str
) -> None:
    # Select popups ignore clicks on Wayland: https://bugreports.qt.io/browse/QTBUG-147154
    if should_use_xwayland(environment, qt_version):
        environment[PLATFORM_VARIABLE] = "xcb"
