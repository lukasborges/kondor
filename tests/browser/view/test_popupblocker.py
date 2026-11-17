from collections.abc import Iterator

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.settings.settings import Settings
from kondor.site.sitesettings import SiteSettings
from tests.extensions.pageserver import PageServer
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.usefixtures("window")
LOAD_TIMEOUT = 30000
TABS_WITH_POPUP = 2
SETTLE_MS = 1500
SIZE = 300
TIMER_PAGE = b"""<html><head><title>timer</title></head><body><script>
setTimeout(() => window.open('/popup', '_blank'), 200);
</script></body></html>"""
CLICK_PAGE = (
    b"<html><head><title>click</title></head><body style='margin:0'>"
    b"<button style='width:300px;height:300px' onclick=\"window.open('/popup', '_blank')\">"
    b"open</button></body></html>"
)
POPUP_PAGE = b"<html><head><title>popup</title></head><body>popup</body></html>"
SCENE_QML = """
import QtQuick
import Kondor

Item {
    width: 300
    height: 300
    Repeater {
        model: testTabModel
        delegate: WebViewTab {
            width: 300
            height: 300
            tabModel: testTabModel
            browserActions: ({})
        }
    }
}
"""


@pytest.fixture
def model(qapp: object, isolated_profile: object) -> Iterator[TabModel]:
    tab_model = TabModel()
    yield tab_model
    tab_model.deleteLater()


@pytest.fixture
def window(model: TabModel, kondor_engine: QQmlEngine) -> Iterator[QQuickWindow]:
    kondor_engine.rootContext().setContextProperty("testTabModel", model)
    component = load_component(kondor_engine, SCENE_QML)
    item = component.create()
    assert item is not None, error_text(component)
    assert isinstance(item, QQuickItem)
    quick_window = QQuickWindow()
    quick_window.resize(SIZE, SIZE)
    item.setParentItem(quick_window.contentItem())
    quick_window.show()
    yield quick_window
    quick_window.close()
    item.deleteLater()


@pytest.fixture
def server() -> Iterator[PageServer]:
    pages = {"/": TIMER_PAGE, "/click": CLICK_PAGE, "/popup": POPUP_PAGE}
    page_server = PageServer(pages)
    yield page_server
    release(page_server)


@pytest.fixture(autouse=True)
def blocking_on_and_no_exceptions(qapp: object) -> Iterator[None]:
    Settings.instance().setProperty("blockPopups", True)
    SiteSettings.instance().setPopupsAllowed("127.0.0.1", False)
    yield
    SiteSettings.instance().setPopupsAllowed("127.0.0.1", False)
    Settings.instance().setProperty("blockPopups", True)


class Browser:
    def __init__(self, model: TabModel, server: PageServer, qtbot: QtBot) -> None:
        self.model = model
        self.server = server
        self.qtbot = qtbot

    def open_page(self, path: str) -> Tab:
        tab = self.model.addTab()
        tab.navigateTo(self.server.url(path))
        return tab

    def wait_for_pop_up_tab(self) -> None:
        self.qtbot.waitUntil(lambda: self.model.rowCount() == TABS_WITH_POPUP, timeout=LOAD_TIMEOUT)

    def wait_for_title(self, tab: Tab, title: str) -> None:
        self.qtbot.waitUntil(lambda: tab.title == title, timeout=LOAD_TIMEOUT)


@pytest.fixture
def browser(model: TabModel, server: PageServer, qtbot: QtBot) -> Browser:
    return Browser(model, server, qtbot)


def test_timer_pop_up_is_blocked_and_listed(browser: Browser) -> None:
    tab = browser.open_page("/")
    browser.qtbot.waitUntil(lambda: bool(tab.popups.blockedUrls), timeout=LOAD_TIMEOUT)
    assert tab.popups.blockedUrls == [browser.server.url("/popup").toString()]
    assert browser.model.rowCount() == 1


def test_allowed_site_opens_the_timer_pop_up(browser: Browser) -> None:
    SiteSettings.instance().setPopupsAllowed("127.0.0.1", True)
    browser.open_page("/")
    browser.wait_for_pop_up_tab()


def test_nothing_is_blocked_when_blocking_is_off(browser: Browser) -> None:
    Settings.instance().setProperty("blockPopups", False)
    tab = browser.open_page("/")
    browser.wait_for_pop_up_tab()
    assert tab.popups.blockedUrls == []


def test_click_pop_up_opens(browser: Browser, window: QQuickWindow) -> None:
    tab = browser.open_page("/click")
    browser.wait_for_title(tab, "click")
    browser.qtbot.wait(SETTLE_MS)
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(SIZE // 2, SIZE // 2))
    browser.wait_for_pop_up_tab()
    assert tab.popups.blockedUrls == []
