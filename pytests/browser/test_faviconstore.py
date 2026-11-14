from collections.abc import Iterator

import pytest
from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.browser.favicons.faviconimageprovider import FaviconImageProvider
from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.core.database import sql
from kondor.history.historymanager import HistoryManager
from pytests.browser.fakefaviconprovider import FakeFaviconProvider
from pytests.history.historyrows import now_ms

AGE_FAVICON = "UPDATE favicons SET updated_at = ? WHERE host = ?"
FAVICON_COUNT = "SELECT COUNT(*) FROM favicons"


@pytest.fixture
def store(qapp: object) -> FaviconStore:
    assert sql.run("DELETE FROM favicons") is not None
    return FaviconStore.instance()


@pytest.fixture
def favicon_engine(
    store: FaviconStore, kondor_types: None, qml_engine: QQmlEngine
) -> Iterator[QQmlEngine]:
    provider = FakeFaviconProvider(make_image(Qt.GlobalColor.red, 64))
    qml_engine.addImageProvider("favicon", provider)
    store.attach_engine(qml_engine)
    yield qml_engine
    store.attach_engine(None)


def make_image(color: Qt.GlobalColor, size: int = 4) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(color)
    return image


def favicon_count() -> int:
    query = sql.run(FAVICON_COUNT)
    return int(query.value(0)) if query is not None and query.next() else -1


def test_stores_and_looks_up_by_host(store: FaviconStore) -> None:
    store.store_image("kde.org", make_image(Qt.GlobalColor.red))
    image = store.image_for_host("kde.org")
    assert not image.isNull()
    assert image.size() == QSize(4, 4)
    assert image.pixelColor(0, 0) == QColor(Qt.GlobalColor.red)
    assert store.image_for_host("example.org").isNull()


def test_replaces_only_when_bytes_change(store: FaviconStore) -> None:
    red = make_image(Qt.GlobalColor.red)
    store.store_image("kde.org", red)
    revision = store.current_revision()
    store.store_image("kde.org", red)
    assert store.current_revision() == revision
    store.store_image("kde.org", make_image(Qt.GlobalColor.blue))
    assert store.current_revision() == revision + 1
    assert store.image_for_host("kde.org").pixelColor(0, 0) == QColor(Qt.GlobalColor.blue)


def test_clear_history_since_keeps_older_favicons(store: FaviconStore) -> None:
    now = now_ms()
    store.store_image("recent.example", make_image(Qt.GlobalColor.red))
    store.store_image("old.example", make_image(Qt.GlobalColor.blue))
    assert sql.run(AGE_FAVICON, (now - 100000, "old.example")) is not None
    HistoryManager.instance().clearSince(now - 1000)
    assert store.image_for_host("recent.example").isNull()
    assert not store.image_for_host("old.example").isNull()


def test_clear_all_removes_every_favicon(store: FaviconStore) -> None:
    store.store_image("kde.org", make_image(Qt.GlobalColor.red))
    store.store_image("example.org", make_image(Qt.GlobalColor.blue))
    store.clear_all()
    assert store.image_for_host("kde.org").isNull()
    assert store.image_for_host("example.org").isNull()


def test_clear_history_also_clears_favicons(store: FaviconStore) -> None:
    store.store_image("kde.org", make_image(Qt.GlobalColor.red))
    HistoryManager.instance().addVisit(QUrl("https://kde.org/"), "KDE")
    HistoryManager.instance().clearAll()
    assert store.image_for_host("kde.org").isNull()


def test_store_saves_the_provider_icon_scaled_to_32(
    store: FaviconStore, favicon_engine: QQmlEngine, qtbot: QtBot
) -> None:
    page, icon = QUrl("https://kde.org/"), QUrl("image://favicon/https://kde.org/icon.png")
    with qtbot.waitSignal(store.revisionChanged, timeout=5000):
        store.store(page, icon)
    assert store.image_for_host("kde.org").size() == QSize(32, 32)


def test_store_ignores_other_pages_and_sources(
    store: FaviconStore, favicon_engine: QQmlEngine, qtbot: QtBot
) -> None:
    icon = QUrl("image://favicon/https://kde.org/icon.png")
    store.store(QUrl("about:blank"), icon)
    store.store(QUrl("file:///tmp/page.html"), icon)
    store.store(QUrl("https://kde.org/"), QUrl("https://kde.org/icon.png"))
    qtbot.wait(50)
    assert favicon_count() == 0


def test_image_provider_serves_the_host_of_the_page_url(store: FaviconStore) -> None:
    store.store_image("kde.org", make_image(Qt.GlobalColor.red))
    size = QSize()
    image = FaviconImageProvider().requestImage("https://kde.org/a?b", size, QSize())
    assert image.pixelColor(0, 0) == QColor(Qt.GlobalColor.red)
    assert size == QSize(4, 4)
