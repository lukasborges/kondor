from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from kondor.browser.favicons.faviconstore import FaviconStore


class FaviconImageProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id: str, size: QSize, requestedSize: QSize) -> QImage:  # noqa: A002, N803
        image = FaviconStore.instance().image_for_host(QUrl(id).host())
        if not image.isNull():
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image
