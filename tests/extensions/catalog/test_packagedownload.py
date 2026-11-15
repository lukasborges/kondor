from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager
from pytestqt.qtbot import QtBot

from kondor.extensions.catalog.catalogentry import CatalogEntry
from kondor.extensions.install.packagedownload import PackageDownload
from tests.extensions.extensionsharness import sample_package, sha256_of

WAIT_MILLISECONDS = 10000


def download(qtbot: QtBot, entry: CatalogEntry) -> tuple[str, str]:
    network = QNetworkAccessManager()
    task = PackageDownload(network, None)
    with qtbot.waitSignal(task.finished, timeout=WAIT_MILLISECONDS) as blocker:
        task.start(entry)
    network.deleteLater()
    args: Any = blocker.args
    return str(args[0]), str(args[1])


def entry_for(path: str, **changes: Any) -> CatalogEntry:
    entry = CatalogEntry(
        id="sample",
        package=QUrl.fromLocalFile(path),
        sha256=sha256_of(path),
        size=Path(path).stat().st_size,
    )
    for name, value in changes.items():
        setattr(entry, name, value)
    return entry


def test_downloads_into_a_kept_temporary_package(qtbot: QtBot, work: str) -> None:
    path, error = download(qtbot, entry_for(sample_package(work)))
    assert error == ""
    assert path.endswith(".kondorext")
    assert Path(path).is_file()
    Path(path).unlink()


def test_checksum_mismatch_removes_the_file(qtbot: QtBot, work: str) -> None:
    path, error = download(qtbot, entry_for(sample_package(work), sha256="0" * 64))
    assert path == ""
    assert "checksum" in error


def test_body_above_the_advertised_size_is_refused(qtbot: QtBot, work: str) -> None:
    path, error = download(qtbot, entry_for(sample_package(work), size=10))
    assert path == ""
    assert error == "The package is larger than expected"


def test_missing_package_reports_the_network_error(qtbot: QtBot, work: str) -> None:
    path, error = download(qtbot, entry_for(sample_package(work), package=QUrl("file:///none.x")))
    assert path == ""
    assert error != ""
