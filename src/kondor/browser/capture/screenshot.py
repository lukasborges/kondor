from PySide6.QtCore import QDateTime, QDir, QObject, QUrl, Slot
from PySide6.QtGui import QGuiApplication, QImage

from kondor.core.filehelper import sanitized_file_name

TIMESTAMP_FORMAT = "yyyy-MM-dd hh.mm.ss"


def screenshot_file_name(title: str, moment: QDateTime) -> str:
    return f"{sanitized_file_name(title)} {moment.toString(TIMESTAMP_FORMAT)}.png"


class Screenshot(QObject):
    _instance: "Screenshot | None" = None

    @classmethod
    def instance(cls) -> "Screenshot":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(QImage)
    def copyToClipboard(self, image: QImage) -> None:
        QGuiApplication.clipboard().setImage(image)

    @Slot(str, str, result=QUrl)
    def suggestedFileUrl(self, directory: str, title: str) -> QUrl:
        name = screenshot_file_name(title, QDateTime.currentDateTime())
        return QUrl.fromLocalFile(QDir(directory).filePath(name))
