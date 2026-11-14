import os
from pathlib import Path

from PySide6.QtCore import QUrl

from kondor.passwords.csvimport.passwordimportfile import MAX_IMPORT_BYTES, read_import_file


def local_url(path: Path) -> QUrl:
    return QUrl.fromLocalFile(str(path))


def test_rejects_files_over_the_size_limit(tmp_path: Path) -> None:
    file = tmp_path / "passwords.csv"
    file.touch()
    os.truncate(file, MAX_IMPORT_BYTES + 1)
    result = read_import_file(local_url(file))
    assert result.error == "tooLarge"
    assert result.data == b""


def test_rejects_missing_and_remote_files() -> None:
    missing = QUrl.fromLocalFile("/nonexistent/passwords.csv")
    remote = QUrl("https://example.com/passwords.csv")
    assert read_import_file(missing).error == "unreadable"
    assert read_import_file(remote).error == "unreadable"


def test_reads_small_files(tmp_path: Path) -> None:
    file = tmp_path / "passwords.csv"
    file.write_bytes(b"a,b\n")
    result = read_import_file(local_url(file))
    assert result.error == ""
    assert result.data == b"a,b\n"
