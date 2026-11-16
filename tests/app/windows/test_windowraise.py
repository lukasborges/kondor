from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlEngine

from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.windows import windowlaunch
from kondor.app.windows.windowcontents import WindowContents
from kondor.extensions.extensionmanager import ExtensionManager
from tests.app.windows.windowstub import StubWindowManager


@pytest.fixture
def manager(kondor_types: None, qml_engine: QQmlEngine) -> Iterator[StubWindowManager]:
    stub = StubWindowManager(qml_engine)
    yield stub
    stub.release_windows()


def test_manage_request_does_not_raise_the_browser_window(
    manager: StubWindowManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    raised: list[QObject] = []
    monkeypatch.setattr(windowlaunch, "raise_window", lambda window, token: raised.append(window))
    manager.create_window(WindowContents())

    manager.show_extensions_settings()

    assert raised == []


def test_extension_package_does_not_raise_the_browser_window(
    manager: StubWindowManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    raised: list[QObject] = []
    monkeypatch.setattr(windowlaunch, "raise_window", lambda window, token: raised.append(window))
    monkeypatch.setattr(ExtensionManager.instance(), "inspectFile", lambda path: None)
    manager.create_window(WindowContents())

    manager.handle_single_instance_message(
        SingleInstanceMessage(urls=[QUrl.fromLocalFile("/tmp/a.kondorext")])
    )

    assert raised == []
