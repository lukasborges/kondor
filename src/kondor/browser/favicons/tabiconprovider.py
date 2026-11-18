from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QImage
from PySide6.QtQuick import (
    QQuickAsyncImageProvider,
    QQuickImageResponse,
    QQuickTextureFactory,
)

from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.browser.favicons.responsefollower import follow_image


class TabIconResponse(QQuickImageResponse):
    def __init__(self) -> None:
        super().__init__()
        self._image = QImage()

    def textureFactory(self) -> QQuickTextureFactory:  # noqa: N802
        return QQuickTextureFactory.textureFactoryForImage(self._image)

    def finish_with(self, image: QImage) -> None:
        self._image = image
        self.finished.emit()

    def finish_later_with(self, image: QImage) -> None:
        QTimer.singleShot(0, lambda: self.finish_with(image))


class TabIconProvider(QQuickAsyncImageProvider):
    def __init__(self) -> None:
        super().__init__()
        self._images: dict[str, QImage] = {}

    def requestImageResponse(  # noqa: N802
        self,
        id: str,
        requestedSize: QSize,  # noqa: A002, N803
    ) -> QQuickImageResponse:
        response = TabIconResponse()
        cached = self._images.get(id)
        if cached is not None:
            response.finish_later_with(cached)
        else:
            self.request_from_qt(id, response)
        return response

    def request_from_qt(self, icon_id: str, response: TabIconResponse) -> None:
        qt_response = FaviconStore.instance().request_awake_icon(icon_id)
        if qt_response is None:
            response.finish_later_with(QImage())
        else:
            self.forward(qt_response, (icon_id, response))

    def forward(
        self, qt_response: QQuickImageResponse, target: tuple[str, TabIconResponse]
    ) -> None:
        follow_image(qt_response, lambda image: self.complete(image, target))

    def complete(self, image: QImage, target: tuple[str, TabIconResponse]) -> None:
        icon_id, response = target
        if not image.isNull():
            self._images[icon_id] = image
        response.finish_with(image)
