from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Q_ARG, QMetaObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.tab import Tab
from kondor.extensions.bridge.extensionbridge import ExtensionBridge
from tests.extensions.pageserver import PageServer

WINDOW_SIZE = (400, 300)
LOAD_TIMEOUT = 30000
ATTRIBUTE_TIMEOUT = 10000
RUN_TIMEOUT = 5000
PAGE_VIEW_QML = """
import QtQuick
import QtWebEngine
import QtWebChannel
WebEngineView {
    id: view
    property var result
    property bool done: false
    function registerApi(api) { channel.registerObject("kondorExtensions", api) }
    property bool loaded: false
    onLoadingChanged: function(info) {
        if (info.status === WebEngineLoadingInfo.LoadSucceededStatus) loaded = true
    }
    function load(address) { loaded = false; url = address }
    width: 400; height: 300
    webChannel: channel
    webChannelWorld: WebEngineScript.ApplicationWorld
    WebChannel { id: channel }
    function run(code) {
        done = false; result = undefined
        runJavaScript(code, WebEngineScript.MainWorld, function(r) { result = r; done = true })
    }
}
"""


@dataclass
class Page:
    view: QQuickItem
    tab: Tab
    bridge: ExtensionBridge
    qtbot: QtBot


class PageHost:
    def __init__(
        self, qtbot: QtBot, server: PageServer, normal_profile: QQuickWebEngineProfile
    ) -> None:
        self.qtbot = qtbot
        self.server = server
        self.normal_profile = normal_profile
        self.private_profile = ProfileManager.instance().createPrivateProfile()
        self.engine = QQmlEngine()
        self.window = QQuickWindow()
        self.window.resize(*WINDOW_SIZE)
        self.window.show()
        self.views: list[QQuickItem] = []
        self.components: list[QQmlComponent] = []

    def open_normal(self, path: str = "/") -> Page:
        return self.open_loaded(self.normal_profile, path)

    def open_private(self, path: str = "/") -> Page:
        return self.open_loaded(self.private_profile, path)

    def open_loaded(self, profile: QQuickWebEngineProfile, path: str) -> Page:
        page = self.open(profile, self.server.url(path))
        wait_loaded(page)
        return page

    def open(self, profile: QQuickWebEngineProfile, url: QUrl) -> Page:
        view = self.create_view(profile)
        view.setParentItem(self.window.contentItem())
        self.views.append(view)
        tab = Tab(profile, view)
        bridge = ExtensionBridge(view)
        bridge.tab = tab
        register_page_api(view, bridge)
        load_url(view, url)
        return Page(view, tab, bridge, self.qtbot)

    def create_view(self, profile: QQuickWebEngineProfile) -> QQuickItem:
        component = QQmlComponent(self.engine)
        component.setData(PAGE_VIEW_QML.encode(), QUrl())
        self.components.append(component)
        view = component.createWithInitialProperties({"profile": profile})
        assert view is not None, component.errorString()
        return view

    def close(self) -> None:
        for view in self.views:
            view.deleteLater()
        self.window.close()


def register_page_api(view: QQuickItem, bridge: ExtensionBridge) -> None:
    QMetaObject.invokeMethod(view, "registerApi", Q_ARG("QVariant", bridge.pageApi()))


def load_url(view: QQuickItem, url: QUrl) -> None:
    QMetaObject.invokeMethod(view, "load", Q_ARG("QVariant", url))


def wait_loaded(page: Page) -> None:
    page.qtbot.waitUntil(lambda: bool(page.view.property("loaded")), timeout=LOAD_TIMEOUT)


def evaluate(page: Page, code: str) -> Any:
    QMetaObject.invokeMethod(page.view, "run", Q_ARG("QVariant", code))
    page.qtbot.waitUntil(lambda: bool(page.view.property("done")), timeout=RUN_TIMEOUT)
    return page.view.property("result")


def attribute(page: Page, name: str) -> str:
    code = (
        "document.readyState === 'complete' ? "
        f"document.documentElement.getAttribute('{name}') : 'loading'"
    )
    return str(evaluate(page, code) or "")


def wait_for_attribute(page: Page, name: str, expected: str) -> None:
    page.qtbot.waitUntil(lambda: attribute(page, name) == expected, timeout=ATTRIBUTE_TIMEOUT)


def run_in_application_world(page: Page, script: str) -> None:
    QMetaObject.invokeMethod(
        page.view,
        "runJavaScript",
        Q_ARG(str, script),
        Q_ARG("uint", int(QWebEngineScript.ScriptWorldId.ApplicationWorld)),
    )
