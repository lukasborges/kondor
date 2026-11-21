import shiboken6
from PySide6.QtCore import (
    Property,
    QBuffer,
    QByteArray,
    QDateTime,
    QIODevice,
    QObject,
    QSize,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickAsyncImageProvider, QQuickImageProvider, QQuickImageResponse
from PySide6.QtSql import QSqlQuery

from kondor.browser.favicons.responsefollower import follow_image
from kondor.core.database import sql

MAX_ICON_SIZE = 32
PROVIDER_ID = "favicon"
PROVIDER_PREFIX = "image://favicon/"
WEB_SCHEMES = ("http", "https")
PNG_FORMAT = "PNG"
SELECT_IMAGE = "SELECT image FROM favicons WHERE host = ?"
STORE_IMAGE = "INSERT OR REPLACE INTO favicons (host, image, updated_at) VALUES (?, ?, ?)"
DELETE_ALL = "DELETE FROM favicons"
DELETE_SINCE = "DELETE FROM favicons WHERE updated_at >= ?"


def provider_icon_id(icon_source: QUrl) -> str:
    source = icon_source.toString()
    return source.removeprefix(PROVIDER_PREFIX) if source.startswith(PROVIDER_PREFIX) else ""


def scaled_to_icon_size(image: QImage) -> QImage:
    if image.width() <= MAX_ICON_SIZE and image.height() <= MAX_ICON_SIZE:
        return image
    aspect, mode = Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
    return image.scaled(MAX_ICON_SIZE, MAX_ICON_SIZE, aspect, mode)


def encode_png(image: QImage) -> QByteArray | None:
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly) or not image.save(buffer, PNG_FORMAT):
        return None
    buffer.close()
    return data


def stored_bytes(host: str) -> QByteArray | None:
    query = sql.run(SELECT_IMAGE, (host,))
    if query is None or not query.next():
        return None
    return QByteArray(query.value(0))


def async_provider(provider: QQuickImageProvider | None) -> QQuickAsyncImageProvider | None:
    if provider is None or isinstance(provider, QQuickAsyncImageProvider):
        return provider
    pointer = shiboken6.getCppPointer(provider)[0]
    shiboken6.invalidate(provider)
    return shiboken6.wrapInstance(pointer, QQuickAsyncImageProvider)


def has_rows_affected(query: QSqlQuery | None) -> bool:
    return query is not None and query.numRowsAffected() > 0


class FaviconStore(QObject):
    revisionChanged = Signal()
    _instance: "FaviconStore | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._engine: QQmlEngine | None = None
        self._revision = 0
        self._sleeping_icons: dict[int, str] = {}

    @classmethod
    def instance(cls) -> "FaviconStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def current_revision(self) -> int:
        return self._revision

    revision = Property(int, current_revision, notify=revisionChanged)

    def attach_engine(self, engine: QQmlEngine | None) -> None:
        self._engine = engine

    @Slot(QUrl, QUrl)
    def store(self, pageUrl: QUrl, iconSource: QUrl) -> None:  # noqa: N803
        icon_id = provider_icon_id(iconSource)
        if self._engine is None or pageUrl.scheme() not in WEB_SCHEMES or not icon_id:
            return
        if icon_id in self._sleeping_icons.values():
            return
        response = self.request_icon(self._engine, icon_id)
        if response is not None:
            self.follow_response(response, pageUrl.host())

    # Qt's favicon provider can pick a sleeping view of the same icon and crash in
    # WebContentsAdapter::icon(): https://github.com/lukasborges/kondor-browser/issues/390
    @Slot(QObject, QUrl)
    def markSleeping(self, view: QObject, iconSource: QUrl) -> None:  # noqa: N802, N803
        self._sleeping_icons[shiboken6.getCppPointer(view)[0]] = provider_icon_id(iconSource)

    @Slot(QObject)
    def markAwake(self, view: QObject) -> None:  # noqa: N802
        self._sleeping_icons.pop(shiboken6.getCppPointer(view)[0], None)

    def request_awake_icon(self, icon_id: str) -> QQuickImageResponse | None:
        if self._engine is None or icon_id in self._sleeping_icons.values():
            return None
        return self.request_icon(self._engine, icon_id)

    def request_icon(self, engine: QQmlEngine, icon_id: str) -> QQuickImageResponse | None:
        provider = async_provider(engine.imageProvider(PROVIDER_ID))
        if provider is None:
            return None
        return provider.requestImageResponse(icon_id, QSize(MAX_ICON_SIZE, MAX_ICON_SIZE))

    def follow_response(self, response: QQuickImageResponse, host: str) -> None:
        follow_image(response, lambda image: self.store_scaled(host, image))

    def store_scaled(self, host: str, image: QImage) -> None:
        if not image.isNull():
            self.store_image(host, scaled_to_icon_size(image))

    def store_image(self, host: str, image: QImage) -> None:
        if not host or image.isNull():
            return
        data = encode_png(image)
        if data is None or stored_bytes(host) == data:
            return
        now = QDateTime.currentMSecsSinceEpoch()
        if sql.run(STORE_IMAGE, (host, data, now)) is not None:
            self.bump_revision()

    def clear_all(self) -> None:
        self.bump_revision_if_rows_affected(sql.run(DELETE_ALL))

    def clear_since(self, msecs_since_epoch: int) -> None:
        self.bump_revision_if_rows_affected(sql.run(DELETE_SINCE, (msecs_since_epoch,)))

    @Slot(QUrl, result=bool)
    def hasIcon(self, pageUrl: QUrl) -> bool:  # noqa: N802, N803
        return not self.image_for_host(pageUrl.host()).isNull()

    def image_for_host(self, host: str) -> QImage:
        data = stored_bytes(host) if host else None
        image = QImage()
        if data is None or not image.loadFromData(data, PNG_FORMAT):
            return QImage()
        return image

    def bump_revision(self) -> None:
        self._revision += 1
        self.revisionChanged.emit()

    def bump_revision_if_rows_affected(self, query: QSqlQuery | None) -> None:
        if has_rows_affected(query):
            self.bump_revision()
