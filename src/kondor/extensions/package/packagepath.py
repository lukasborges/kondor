from PySide6.QtCore import QDir, QFileInfo


def has_forbidden_character(path: str) -> bool:
    return path.startswith("/") or "\\" in path or QDir.isAbsolutePath(path) or ":" in path


def is_unsafe_part(part: str) -> bool:
    return part in {"", ".."}


def is_safe_relative_path(path: str) -> bool:
    if not path or has_forbidden_character(path):
        return False
    return not any(is_unsafe_part(part) for part in path.split("/"))


def package_file_error(directory: str, path: str, where: str) -> str:
    if not is_safe_relative_path(path):
        return f"manifest.json: {where}: invalid path: {path}"
    info = QFileInfo(QDir(directory).filePath(path))
    if not info.isFile() or info.isSymLink():
        return f"manifest.json: {where}: file not found: {path}"
    return ""
