import gc
import os
from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.app.commandline.startupargs import StartupArgs
from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.instance.windowactivation import raise_window
from kondor.app.remotecontrol.remotecontrol import RemoteControl
from kondor.app.windows.windowcontents import WindowContents
from kondor.browser.session.sessionmanager import SessionManager
from kondor.browser.session.sessionwindow import SessionTab, SessionWindow
from kondor.core.settings.settings import Settings
from kondor.extensions.extensionmanager import ExtensionManager
from tests.app.windows.windowstub import StubWindowManager

KDE = QUrl("https://kde.org")
TWO_WINDOWS = 2


@pytest.fixture
def manager(kondor_types: None, qml_engine: QQmlEngine) -> Iterator[StubWindowManager]:
    stub = StubWindowManager(qml_engine)
    yield stub
    stub.release_windows()


@pytest.fixture
def startup_args(monkeypatch: pytest.MonkeyPatch) -> StartupArgs:
    args = StartupArgs.instance()
    monkeypatch.setattr(args, "_startup_urls", [])
    monkeypatch.setattr(args, "_startup_private", False)
    return args


def message(**values: object) -> SingleInstanceMessage:
    return SingleInstanceMessage(**values)  # type: ignore[arg-type]


def test_new_window_passes_initial_properties(manager: StubWindowManager) -> None:
    window = manager.newWindow(True, [KDE])

    assert window is not None
    assert window.property("privateWindow") is True
    assert window.property("initialUrls") == [KDE]
    assert window.property("initialCurrentIndex") == -1


def test_window_count_follows_created_and_closed_windows(
    manager: StubWindowManager, qtbot: QtBot
) -> None:
    window = manager.newWindow()
    assert manager.window_count() == 1

    with qtbot.waitSignal(manager.windowCountChanged, timeout=2000):
        manager.closeWindow(window)
        qtbot.wait(10)

    assert manager.window_count() == 0


def test_message_adds_tabs_to_window_of_same_privacy(manager: StubWindowManager) -> None:
    window = manager.create_window(WindowContents())

    manager.handle_single_instance_message(message(urls=[KDE]))

    assert manager.window_count() == 1
    assert window is not None
    assert window.property("addedUrls").toVariant() == ["https://kde.org"]


def test_private_message_never_reuses_a_normal_window(manager: StubWindowManager) -> None:
    normal = manager.create_window(WindowContents())

    manager.handle_single_instance_message(message(urls=[KDE], private_mode=True))

    assert manager.window_count() == TWO_WINDOWS
    assert normal is not None
    assert normal.property("addedUrls").toVariant() == []
    assert manager.window_for_request(True) is not normal


def test_new_window_flag_always_creates_a_window(manager: StubWindowManager) -> None:
    manager.create_window(WindowContents())

    manager.handle_single_instance_message(message(urls=[KDE], new_window=True))

    assert manager.window_count() == TWO_WINDOWS


def test_extension_package_opens_the_extensions_page(
    manager: StubWindowManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    inspected: list[str] = []
    monkeypatch.setattr(ExtensionManager.instance(), "inspectFile", inspected.append)
    window = manager.create_window(WindowContents())

    manager.handle_single_instance_message(message(urls=[QUrl.fromLocalFile("/tmp/a.kondorext")]))

    assert inspected == ["/tmp/a.kondorext"]
    assert window is not None
    assert window.property("openedPages").toVariant() == ["extensions"]


def test_startup_restores_saved_windows(
    manager: StubWindowManager, startup_args: StartupArgs, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved = [
        SessionWindow([SessionTab(KDE, "KDE"), SessionTab(QUrl("https://qt.io"), "Qt")], 1),
        SessionWindow([SessionTab(QUrl("https://example.com"), "Example")], 0),
    ]
    monkeypatch.setattr(SessionManager.instance(), "saved_windows", lambda: saved)
    monkeypatch.setattr(Settings.instance(), "startupBehavior", "restore")

    manager.open_startup_windows()

    assert manager.window_count() == len(saved)
    first = manager.window_for_request(False)
    assert first is not None
    assert first.property("initialCurrentIndex") == 0


def test_startup_without_urls_opens_one_empty_window(
    manager: StubWindowManager, startup_args: StartupArgs
) -> None:
    manager.open_startup_windows()

    assert manager.window_count() == 1


def test_open_window_survives_garbage_collection(manager: StubWindowManager) -> None:
    window = manager.newWindow()
    del window

    gc.collect()

    assert manager.window_count() == 1
    assert manager.window_for_request(False) is not None


def test_raise_window_exports_the_activation_token(
    manager: StubWindowManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("XDG_ACTIVATION_TOKEN", raising=False)
    window = manager.newWindow()
    assert isinstance(window, QObject)

    raise_window(window, b"token-1")

    assert os.environ["XDG_ACTIVATION_TOKEN"] == "token-1"


def test_private_window_is_refused_while_remote_control_is_on(
    manager: StubWindowManager, remote_control: RemoteControl
) -> None:
    remote_control.set_port(9333)

    assert manager.newWindow(True) is None
    assert manager.window_count() == 0


def test_private_message_opens_nothing_while_remote_control_is_on(
    manager: StubWindowManager, remote_control: RemoteControl
) -> None:
    remote_control.set_port(9333)
    normal = manager.create_window(WindowContents())

    manager.handle_single_instance_message(message(urls=[KDE], private_mode=True))

    assert manager.window_count() == 1
    assert normal is not None
    assert normal.property("addedUrls").toVariant() == []


def test_private_message_creates_a_normal_window_when_none_is_open(
    manager: StubWindowManager, remote_control: RemoteControl
) -> None:
    remote_control.set_port(9333)

    manager.handle_single_instance_message(message(urls=[KDE], private_mode=True))

    assert manager.window_count() == 1
    assert manager.window_for_request(False) is not None
