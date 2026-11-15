from collections.abc import Iterator

import pytest
from PySide6.QtCore import QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import captured_messages, error_text, load_component


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


SCENE_QML = """
import QtQuick
import QtWebEngine
import Kondor

Item {
    function reportError() {
        certificateHandler.handle(certificateError)
    }

    CertificateErrorHandler {
        id: certificateHandler
        tab: testTab
        tabModel: testTabModel
        webView: WebEngineView {}
    }

    QtObject {
        id: certificateError
        property url url: "https://expired.example"
        property string description: "The certificate has expired"
        property bool overridable: true
        property bool isMainFrame: true
        function defer() {}
        function rejectCertificate() {}
        function acceptCertificate() {}
    }
}
"""


def load_scene(engine: QQmlEngine, tab: Tab, model: TabModel) -> tuple[QQmlComponent, QObject]:
    engine.rootContext().setContextProperty("testTab", tab)
    engine.rootContext().setContextProperty("testTabModel", model)
    component = load_component(engine, SCENE_QML)
    scene = component.create()
    assert scene is not None, error_text(component)
    return component, scene


def test_main_frame_error_is_reported_to_the_tab_security(
    model: TabModel, kondor_engine: QQmlEngine
) -> None:
    tab = model.addTab()
    tab.setUrl(QUrl("https://expired.example"))
    component, scene = load_scene(kondor_engine, tab, model)
    with captured_messages() as messages:
        QMetaObject.invokeMethod(scene, "reportError")
    assert [m for m in messages if "TypeError" in m] == []
    assert tab.security.certificateErrorPending
    assert tab.security.state == "error"
    assert tab.security.certificateErrorUrl == QUrl("https://expired.example")
    del component
