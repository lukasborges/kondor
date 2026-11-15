from collections.abc import Iterator

import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine
from pytestqt.qtbot import QtBot

from kondor.app.startup.appstartup import set_up_favicons
from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.core.database import sql
from tests.browser.fakefaviconprovider import FakeFaviconProvider

PAGE = QUrl("https://kde.org/")
ICON = QUrl("image://favicon/https://kde.org/icon.png")


@pytest.fixture
def engine(qapp: object) -> Iterator[QQmlApplicationEngine]:
    assert sql.run("DELETE FROM favicons") is not None
    engine = QQmlApplicationEngine()
    image = QImage(4, 4, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.red)
    engine.addImageProvider("favicon", FakeFaviconProvider(image))
    yield engine
    FaviconStore.instance().attach_engine(None)


def test_startup_lets_the_store_save_page_favicons(
    engine: QQmlApplicationEngine, qtbot: QtBot
) -> None:
    set_up_favicons(engine)
    store = FaviconStore.instance()
    with qtbot.waitSignal(store.revisionChanged, timeout=5000):
        store.store(PAGE, ICON)
    assert store.hasIcon(PAGE)
