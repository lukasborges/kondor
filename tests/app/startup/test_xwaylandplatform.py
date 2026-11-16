import pytest

from kondor.app.startup.xwaylandplatform import (
    use_xwayland_when_qt_breaks_wayland_popups,
)

AFFECTED = "6.11.2"


def platform_after(environment: dict[str, str], qt_version: str = AFFECTED) -> str | None:
    use_xwayland_when_qt_breaks_wayland_popups(environment, qt_version)
    return environment.get("QT_QPA_PLATFORM")


def test_chooses_xwayland_when_wayland_display_is_set() -> None:
    assert platform_after({"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}) == "xcb"


def test_chooses_xwayland_when_session_type_is_wayland() -> None:
    assert platform_after({"XDG_SESSION_TYPE": "wayland", "DISPLAY": ":0"}) == "xcb"


def test_stays_on_wayland_when_no_wayland_session() -> None:
    assert platform_after({"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"}) is None


def test_stays_on_wayland_when_no_x_server() -> None:
    assert platform_after({"WAYLAND_DISPLAY": "wayland-0"}) is None


def test_keeps_platform_chosen_by_user() -> None:
    environment = {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0", "QT_QPA_PLATFORM": "wayland"}
    assert platform_after(environment) == "wayland"


@pytest.mark.parametrize("qt_version", ["6.10.3", "6.12.0", "7.0.0"])
def test_stays_on_wayland_when_qt_is_not_the_affected_series(qt_version: str) -> None:
    environment = {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}
    assert platform_after(environment, qt_version) is None


def test_chooses_xwayland_on_any_qt611_release() -> None:
    assert platform_after({"WAYLAND_DISPLAY": "w", "DISPLAY": ":0"}, "6.11.0") == "xcb"
