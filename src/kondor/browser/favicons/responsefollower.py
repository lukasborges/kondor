from collections.abc import Callable

import shiboken6
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageResponse

_pending: dict[int, QQuickImageResponse] = {}


def response_at(pointer: int) -> QQuickImageResponse:
    return shiboken6.wrapInstance(pointer, QQuickImageResponse)


def image_of(response: QQuickImageResponse) -> QImage:
    factory = response.textureFactory()
    return QImage() if factory is None else factory.image()


def follow_image(response: QQuickImageResponse, on_image: Callable[[QImage], None]) -> None:
    pointer = shiboken6.getCppPointer(response)[0]
    _pending[pointer] = response
    response.finished.connect(lambda: deliver_image(pointer, on_image))


def deliver_image(pointer: int, on_image: Callable[[QImage], None]) -> None:
    response = response_at(pointer)
    image = image_of(response)
    response.deleteLater()
    del _pending[pointer]
    on_image(image)
