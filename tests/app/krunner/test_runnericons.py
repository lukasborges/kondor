from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QImage

from kondor.app.krunner.runnericons import icon_data
from kondor.browser.favicons.faviconstore import FaviconStore


def test_stored_favicon_gives_rgba_icon_data(fresh_database: Path) -> None:
    image = QImage(4, 4, QImage.Format.Format_ARGB32)
    image.fill(QColor("red"))
    FaviconStore.instance().store_image("kde.org", image)

    width, height, stride, has_alpha, bits, channels, pixels = icon_data(QUrl("https://kde.org/x"))  # type: ignore[misc]

    assert (width, height, stride, has_alpha, bits, channels) == (4, 4, 16, True, 8, 4)
    assert pixels[:4] == bytes([255, 0, 0, 255])
    assert len(pixels) == 4 * 4 * 4


def test_unknown_host_gives_none(fresh_database: Path) -> None:
    assert icon_data(QUrl("https://unknown.example/")) is None
