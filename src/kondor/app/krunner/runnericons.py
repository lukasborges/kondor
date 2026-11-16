from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage

from kondor.browser.favicons.faviconstore import FaviconStore

FALLBACK_ICONS = {
    "tab": "internet-web-browser",
    "bookmark": "bookmarks",
    "history": "view-history",
}
BITS_PER_SAMPLE = 8
CHANNELS = 4

IconData = tuple[int, int, int, bool, int, int, bytes]


def encode_icon(image: QImage) -> IconData:
    size = (image.width(), image.height(), image.bytesPerLine())
    pixels = bytes(image.constBits())[: image.sizeInBytes()]
    return (*size, True, BITS_PER_SAMPLE, CHANNELS, pixels)


def icon_data(url: QUrl) -> IconData | None:
    image = FaviconStore.instance().image_for_host(url.host())
    if image.isNull():
        return None
    return encode_icon(image.convertToFormat(QImage.Format.Format_RGBA8888))


def fallback_icon(kind: str) -> str:
    return FALLBACK_ICONS[kind]
