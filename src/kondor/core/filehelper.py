from PySide6.QtCore import QDir, QFile, QIODevice, QObject, QTemporaryDir, QUrl, Slot
from PySide6.QtGui import QDesktopServices

FORBIDDEN_CHARACTERS = '/\\:*?"<>|'
FIRST_PRINTABLE = 0x20
MAX_NAME_UNITS = 100
FALLBACK_NAME = "page"
QT_WHITESPACE = (
    "\t\n\v\f\r \x85\xa0 "
    + "".join(chr(code) for code in range(0x2000, 0x200B))
    + "    　"
)
READER_RESOURCES = ("Readability.js", "Readability-readerable.js", "template.html")
READER_FOLDER = ":/reader/"


def is_forbidden(character: str) -> bool:
    return character in FORBIDDEN_CHARACTERS or ord(character) < FIRST_PRINTABLE


def replace_forbidden(name: str) -> str:
    return "".join("_" if is_forbidden(character) else character for character in name)


def left_utf16(text: str, units: int) -> str:
    encoded = text.encode("utf-16-le", errors="surrogatepass")[: units * 2]
    return encoded.decode("utf-16-le", errors="ignore")


def sanitized_file_name(title: str) -> str:
    name = replace_forbidden(title.strip(QT_WHITESPACE))
    name = left_utf16(name, MAX_NAME_UNITS).strip(QT_WHITESPACE)
    return name or FALLBACK_NAME


def read_utf8_resource(path: str) -> str:
    file = QFile(path)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        return ""
    return bytes(file.readAll().data()).decode("utf-8", errors="replace")


class FileHelper(QObject):
    _instance: "FileHelper | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._temp_dir = QTemporaryDir(QDir.tempPath() + "/kondor-print-XXXXXX")
        self._counter = 0

    @classmethod
    def instance(cls) -> "FileHelper":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(str, result=str)
    def sanitizeFileName(self, title: str) -> str:
        return sanitized_file_name(title)

    @Slot(str, str, str, result=QUrl)
    def suggestedFileUrl(self, directory: str, title: str, extension: str) -> QUrl:
        file_name = sanitized_file_name(title) + extension
        return QUrl.fromLocalFile(QDir(directory).filePath(file_name))

    @Slot(result=str)
    def tempPdfPath(self) -> str:
        if not self._temp_dir.isValid():
            return ""
        self._counter += 1
        return str(self._temp_dir.filePath(f"print-{self._counter}.pdf"))

    @Slot(str, result=str)
    def readerResource(self, name: str) -> str:
        if name not in READER_RESOURCES:
            return ""
        return read_utf8_resource(READER_FOLDER + name)

    @Slot(str, result=bool)
    def openFile(self, path: str) -> bool:
        return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(path)))
