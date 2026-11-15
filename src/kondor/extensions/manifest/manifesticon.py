from PySide6.QtCore import QDir, QUrl
from PySide6.QtGui import QImage

from kondor.extensions.package.packagepath import package_file_error

MINIMUM_PNG_SIZE = 64
DEFAULT_ICON = "preferences-plugin"


def ends_with_ignoring_case(icon: str, suffix: str) -> bool:
    return icon.lower().endswith(suffix)


def is_image_file(icon: str) -> bool:
    return ends_with_ignoring_case(icon, ".svg") or ends_with_ignoring_case(icon, ".png")


def is_too_small(image: QImage) -> bool:
    return bool(image.isNull()) or min(image.width(), image.height()) < MINIMUM_PNG_SIZE


def image_error(directory: str, icon: str) -> str:
    error = package_file_error(directory, icon, "icon")
    if error or not ends_with_ignoring_case(icon, ".png"):
        return error
    if not is_too_small(QImage(QDir(directory).filePath(icon))):
        return ""
    return f"manifest.json: icon: a PNG icon must be at least 64 px: {icon}"


def resolve_manifest_icon(directory: str, icon: str) -> tuple[str | None, str]:
    if not icon:
        return DEFAULT_ICON, ""
    if not is_image_file(icon):
        return icon, ""
    error = image_error(directory, icon)
    if error:
        return None, error
    return QUrl.fromLocalFile(QDir(directory).filePath(icon)).toString(), ""
