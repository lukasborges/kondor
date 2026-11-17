from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.browser.tabs.tab import Tab
from kondor.browser.tabs.tabmodel import TabModel
from kondor.core.database import sql
from tests.app.startup.test_favicons_real_page import png_bytes
from tests.browser.view.test_pagesleep import DISCARDED
from tests.extensions.pageserver import PageServer
from tests.qmlsupport import error_text, load_component, release

pytestmark = pytest.mark.no_qt_log

LOAD_TIMEOUT = 30000
SETTLE_MILLISECONDS = 1000
FIRST_VIEW = 0
PAGE_TEMPLATE = (
    '<html><head><title>{name}</title><link rel="icon" href="/{name}.png"></head>'
    "<body>{name}</body></html>"
)
FIRST_PAGE = PAGE_TEMPLATE.format(name="first").encode()
SECOND_PAGE = PAGE_TEMPLATE.format(name="second").encode()
TWO_TABS_QML = """
import QtQuick
import Kondor

Item {
    id: holder
    width: 400; height: 300
    function pageViews(item) {
        const found = item.objectName === "pageView" ? [item] : []
        return found.concat(...Array.from(item.children, pageViews))
    }
    function hidePage(index) { pageViews(holder)[index].visible = false }
    function lifecycle(index) { return pageViews(holder)[index].lifecycleState }
    function iconOf(index) { return pageViews(holder)[index].icon.toString() }
    function showPage(index) { pageViews(holder)[index].visible = true }
    function closeView(index) { holder.children[index].destroy() }
    WebViewTab {
        anchors.fill: parent
        tab: testTab
        tabModel: testModel
        browserActions: null
    }
    WebViewTab {
        anchors.fill: parent
        tab: secondTab
        tabModel: testModel
        browserActions: null
    }
}
"""


class TwoTabs:
    def __init__(self, engine: QQmlEngine, server: PageServer) -> None:
        self.server = server
        self.model = TabModel()
        self.first, self.second = self.model.addTab(), self.model.addTab()
        assert self.first is not None and self.second is not None
        context = engine.rootContext()
        context.setContextProperty("testModel", self.model)
        context.setContextProperty("testTab", self.first)
        context.setContextProperty("secondTab", self.second)
        self.component = load_component(engine, TWO_TABS_QML)
        created = self.component.create()
        assert created is not None, error_text(self.component)
        self.root: QObject = created

    def call(self, name: str, index: int) -> None:
        QMetaObject.invokeMethod(self.root, name, Q_ARG("QVariant", index))

    def lifecycle(self, index: int) -> int:
        result = QMetaObject.invokeMethod(
            self.root, "lifecycle", Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", index)
        )
        return int(result)

    def icon(self, index: int) -> str:
        result = QMetaObject.invokeMethod(
            self.root, "iconOf", Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", index)
        )
        return str(result)

    def release(self) -> None:
        release(self.root)
        release(self.component, self.model, self.server)


def open_page(tab: Tab, page: tuple[QUrl, str], qtbot: QtBot) -> None:
    tab.navigateTo(page[0])
    qtbot.waitUntil(lambda: tab.title == page[1], timeout=LOAD_TIMEOUT)


def favicon_rows() -> int:
    query = sql.run("SELECT COUNT(*) FROM favicons")
    assert query is not None and query.next()
    return int(query.value(0))


@pytest.fixture
def tabs(kondor_engine: QQmlEngine, qtbot: QtBot) -> Iterator[TwoTabs]:
    assert sql.run("DELETE FROM favicons") is not None
    FaviconStore.instance().attach_engine(kondor_engine)
    server = PageServer(
        {
            "/": FIRST_PAGE,
            "/other": SECOND_PAGE,
            "/first.png": png_bytes(),
            "/second.png": png_bytes(),
        }
    )
    tabs = TwoTabs(kondor_engine, server)
    open_page(tabs.second, (server.url().resolved(QUrl("other")), "second"), qtbot)
    open_page(tabs.first, (server.url(), "first"), qtbot)
    qtbot.waitUntil(lambda: favicon_rows() > 0, timeout=LOAD_TIMEOUT)
    yield tabs
    FaviconStore.instance().attach_engine(None)
    tabs.release()


def put_first_tab_to_sleep(tabs: TwoTabs, qtbot: QtBot) -> None:
    qtbot.waitUntil(lambda: tabs.icon(FIRST_VIEW).endswith("/first.png"), timeout=LOAD_TIMEOUT)
    tabs.call("hidePage", FIRST_VIEW)
    tabs.first.sleep.putToSleep()
    qtbot.waitUntil(lambda: tabs.lifecycle(FIRST_VIEW) == DISCARDED, timeout=LOAD_TIMEOUT)
    qtbot.wait(SETTLE_MILLISECONDS)
    assert sql.run("DELETE FROM favicons") is not None


def test_icon_shown_by_a_sleeping_view_is_not_stored(tabs: TwoTabs, qtbot: QtBot) -> None:
    put_first_tab_to_sleep(tabs, qtbot)
    tabs.second.navigateTo(tabs.server.url())
    qtbot.wait(SETTLE_MILLISECONDS)
    assert favicon_rows() == 0


def test_icon_is_stored_again_after_the_view_wakes(tabs: TwoTabs, qtbot: QtBot) -> None:
    put_first_tab_to_sleep(tabs, qtbot)
    tabs.call("showPage", FIRST_VIEW)
    qtbot.waitUntil(lambda: tabs.lifecycle(FIRST_VIEW) != DISCARDED, timeout=LOAD_TIMEOUT)
    assert sql.run("DELETE FROM favicons") is not None
    tabs.second.navigateTo(tabs.server.url())
    qtbot.waitUntil(lambda: favicon_rows() > 0, timeout=LOAD_TIMEOUT)


def test_closing_a_sleeping_view_does_not_crash_the_other_view(tabs: TwoTabs, qtbot: QtBot) -> None:
    put_first_tab_to_sleep(tabs, qtbot)
    tabs.call("closeView", FIRST_VIEW)
    tabs.second.navigateTo(tabs.server.url())
    qtbot.waitUntil(lambda: favicon_rows() > 0, timeout=LOAD_TIMEOUT)
