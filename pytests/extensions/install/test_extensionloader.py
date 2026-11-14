from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.extensions.install.extensionloader import ExtensionLoader
from pytests.extensions.extensionsharness import DATA_ROOT
from pytests.extensions.pageserver import PageServer
from pytests.qmlsupport import captured_messages, error_text, load_component

pytestmark = [
    pytest.mark.no_qt_log,
    pytest.mark.skipif(
        not ExtensionLoader.is_supported(), reason="Qt WebEngine was built without extensions"
    ),
]
TEST_EXTENSION = str(DATA_ROOT / "extension")
EXTENSION_NAME = "Kondor Test Extension"
LOAD_TIMEOUT = 20000
MARKER_VIEW = """
import QtQuick
import QtWebEngine
WebEngineView {
    property string marker: "pending"
    property bool loaded: false
    onLoadingChanged: function(request) {
        if (request.status === WebEngineView.LoadSucceededStatus)
            loaded = true
    }
    property Timer poll: Timer {
        interval: 200; repeat: true; running: parent.loaded && parent.marker !== "ran"
        onTriggered: parent.runJavaScript(
            "document.documentElement.dataset.kondorTest || 'none'",
            function(result) { parent.marker = result })
    }
}
"""


@pytest.fixture
def owner(qapp: object) -> Iterator[QObject]:
    owner = QObject()
    yield owner
    owner.deleteLater()


def find_test_extension(profile: QQuickWebEngineProfile) -> Any:
    for info in profile.extensionManager().extensions():
        if info.name() == EXTENSION_NAME:
            return info
    return None


def load_test_extension(qtbot: Any, owner: QObject) -> tuple[QQuickWebEngineProfile, list[Any]]:
    profile = QQuickWebEngineProfile("kondor-extension-test", owner)
    loader = ExtensionLoader(owner)
    with qtbot.waitSignal(loader.loadFinished, timeout=LOAD_TIMEOUT) as blocker:
        loader.load(profile, [TEST_EXTENSION])
    return profile, blocker.args


def test_loads_an_unpacked_extension(qtbot: Any, owner: QObject) -> None:
    profile, args = load_test_extension(qtbot, owner)
    assert args[1] is True
    info = find_test_extension(profile)
    assert info.isLoaded()
    assert info.name() == EXTENSION_NAME
    assert info.actionPopupUrl().toString().endswith("popup.html")


def test_content_script_runs(qtbot: Any, owner: QObject) -> None:
    profile, _args = load_test_extension(qtbot, owner)
    server = PageServer()
    engine = QQmlEngine(owner)
    component = load_component(engine, MARKER_VIEW)
    view = component.create()
    assert view is not None, error_text(component)
    view.setProperty("profile", profile)
    view.setProperty("url", server.url())
    qtbot.waitUntil(lambda: view.property("marker") == "ran", timeout=LOAD_TIMEOUT)


def test_private_profiles_get_no_extensions(qtbot: Any, owner: QObject) -> None:
    profile = QQuickWebEngineProfile(owner)
    loader = ExtensionLoader(owner)
    with captured_messages() as messages:
        loader.load(profile, [TEST_EXTENSION])
    assert "Extensions are never loaded into private profiles" in messages
    assert find_test_extension(profile) is None
