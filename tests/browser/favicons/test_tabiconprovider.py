from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject, QSize, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageResponse
from pytestqt.qtbot import QtBot

from kondor.browser.favicons.faviconstore import FaviconStore, image_of
from kondor.browser.favicons.tabiconprovider import TabIconProvider
from tests.browser.fakefaviconprovider import FakeFaviconProvider

ICON_ID = "https://kde.org/icon.png"
ICON = QUrl("image://favicon/" + ICON_ID)
SIZE = QSize(16, 16)


@pytest.fixture
def qt_provider(qapp: object) -> Iterator[FakeFaviconProvider]:
    engine = QQmlApplicationEngine()
    image = QImage(4, 4, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.red)
    provider = FakeFaviconProvider(image)
    engine.addImageProvider("favicon", provider)
    FaviconStore.instance().attach_engine(engine)
    yield provider
    FaviconStore.instance().attach_engine(None)


def fetch(provider: TabIconProvider, qtbot: QtBot, icon_id: str = ICON_ID) -> QImage:
    response: QQuickImageResponse = provider.requestImageResponse(icon_id, SIZE)
    with qtbot.waitSignal(response.finished, timeout=5000):
        pass
    return image_of(response)


def sleeping_view(store: FaviconStore) -> QObject:
    view = QObject()
    store.markSleeping(view, ICON)
    return view


def test_awake_icon_is_fetched_from_qt(qt_provider: FakeFaviconProvider, qtbot: QtBot) -> None:
    assert not fetch(TabIconProvider(), qtbot).isNull()
    assert [request[0] for request in qt_provider.requests] == [ICON_ID]


def test_cached_icon_is_not_requested_twice(qt_provider: FakeFaviconProvider, qtbot: QtBot) -> None:
    provider = TabIconProvider()
    fetch(provider, qtbot)
    assert not fetch(provider, qtbot).isNull()
    assert len(qt_provider.requests) == 1


def test_sleeping_icon_never_reaches_qt(qt_provider: FakeFaviconProvider, qtbot: QtBot) -> None:
    view = sleeping_view(FaviconStore.instance())
    fetch(TabIconProvider(), qtbot)
    assert qt_provider.requests == []
    FaviconStore.instance().markAwake(view)


def test_sleeping_icon_is_served_from_memory(
    qt_provider: FakeFaviconProvider, qtbot: QtBot
) -> None:
    provider = TabIconProvider()
    fetch(provider, qtbot)
    view = sleeping_view(FaviconStore.instance())
    assert not fetch(provider, qtbot).isNull()
    assert len(qt_provider.requests) == 1
    FaviconStore.instance().markAwake(view)
