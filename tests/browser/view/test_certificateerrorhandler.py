from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_RETURN_ARG, QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlEngine

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from tests.qmlsupport import captured_messages, error_text, load_component, release


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    release(tab_model)


SCENE_QML = """
import QtQuick
import QtWebEngine
import Kondor

Item {
    function reportError() {
        certificateHandler.handle(certificateError)
    }

    function outcome() {
        return certificateError.outcome
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
        property string outcome: ""
        function defer() {}
        function rejectCertificate() { outcome = "rejected" }
        function acceptCertificate() { outcome = "accepted" }
    }
}
"""


@pytest.fixture
def scenes(model: TabModel, kondor_engine: QQmlEngine) -> Iterator[list[QObject]]:
    kondor_engine.rootContext().setContextProperty("testTabModel", model)
    created: list[QObject] = []
    yield created
    release(*reversed(created))


def load_scene(engine: QQmlEngine, tab: Tab, created: list[QObject]) -> QObject:
    engine.rootContext().setContextProperty("testTab", tab)
    component = load_component(engine, SCENE_QML)
    created.append(component)
    scene = component.create()
    assert scene is not None, error_text(component)
    created.append(scene)
    return scene


def test_main_frame_error_is_reported_to_the_tab_security(
    model: TabModel, kondor_engine: QQmlEngine, scenes: list[QObject]
) -> None:
    tab = model.addTab()
    tab.setUrl(QUrl("https://expired.example"))
    scene = load_scene(kondor_engine, tab, scenes)
    with captured_messages() as messages:
        QMetaObject.invokeMethod(scene, "reportError")
    assert [m for m in messages if "TypeError" in m] == []
    assert tab.security.certificateErrorPending
    assert tab.security.state == "error"
    assert tab.security.certificateErrorUrl == QUrl("https://expired.example")


def report_error_then(tab: Tab, scene: QObject, action: str) -> str:
    QMetaObject.invokeMethod(scene, "reportError")
    getattr(tab.security, action)()
    return str(QMetaObject.invokeMethod(scene, "outcome", Q_RETURN_ARG("QVariant")))


def test_accepting_the_error_accepts_the_deferred_certificate(
    model: TabModel, kondor_engine: QQmlEngine, scenes: list[QObject]
) -> None:
    tab = model.addTab()
    scene = load_scene(kondor_engine, tab, scenes)
    assert report_error_then(tab, scene, "acceptCertificateError") == "accepted"


def test_rejecting_the_error_rejects_the_deferred_certificate(
    model: TabModel, kondor_engine: QQmlEngine, scenes: list[QObject]
) -> None:
    tab = model.addTab()
    scene = load_scene(kondor_engine, tab, scenes)
    assert report_error_then(tab, scene, "rejectCertificateError") == "rejected"
