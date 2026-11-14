from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QImage
from PySide6.QtQuick import (
    QQuickAsyncImageProvider,
    QQuickImageResponse,
    QQuickTextureFactory,
)


class FakeImageResponse(QQuickImageResponse):
    def __init__(self, image: QImage) -> None:
        super().__init__()
        self._image = image
        QTimer.singleShot(0, self.finished.emit)

    def textureFactory(self) -> QQuickTextureFactory:
        return QQuickTextureFactory.textureFactoryForImage(self._image)


class FakeFaviconProvider(QQuickAsyncImageProvider):
    def __init__(self, image: QImage) -> None:
        super().__init__()
        self._image = image
        self.requests: list[tuple[str, QSize]] = []

    def requestImageResponse(self, id: str, requestedSize: QSize) -> QQuickImageResponse:  # noqa: A002, N803
        self.requests.append((id, requestedSize))
        return FakeImageResponse(self._image)
