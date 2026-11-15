from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from kondor.core.notifier import Notifier
from kondor.core.settings.settings import Settings
from kondor.downloads.downloadmanager import DownloadManager
from tests.downloads.fakedownload import FakeDownload, State

Notification = tuple[str, str, str]


@pytest.fixture
def manager(qapp: object, tmp_path: Path) -> Iterator[DownloadManager]:
    settings = Settings.instance()
    previous = settings.property("downloadDirectory")
    settings.setProperty("downloadDirectory", str(tmp_path))
    yield DownloadManager.instance()
    settings.setProperty("downloadDirectory", previous)
    model = DownloadManager.instance().download_model()
    while model.rowCount() > 0:
        model.remove_download(0)


@pytest.fixture
def notifications(monkeypatch: pytest.MonkeyPatch) -> list[Notification]:
    sent: list[Notification] = []

    def record(title: str, body: str, icon: str) -> None:
        sent.append((title, body, icon))

    monkeypatch.setattr(Notifier.instance(), "notify", record)
    return sent


def listed_downloads(manager: DownloadManager) -> list[object]:
    model = manager.download_model()
    return [model.download_at(row) for row in range(model.rowCount())]


def test_handle_request_uses_the_download_directory_and_accepts(
    manager: DownloadManager, tmp_path: Path
) -> None:
    download = FakeDownload()
    manager.handle_request(download.as_request())
    assert download.downloadDirectory() == str(tmp_path)
    assert download.downloadFileName() == "suggested.bin"
    assert download.was_accepted
    assert listed_downloads(manager) == [download]


def test_save_page_download_keeps_its_target(manager: DownloadManager) -> None:
    download = FakeDownload("page.html", is_save_page=True)
    download.setDownloadDirectory("/somewhere")
    manager.handle_request(download.as_request())
    assert download.downloadDirectory() == "/somewhere"
    assert download.downloadFileName() == "page.html"


def test_completed_download_notifies_with_its_file_name(
    manager: DownloadManager, notifications: list[Notification]
) -> None:
    download = FakeDownload("file.zip")
    manager.handle_request(download.as_request())
    download.set_state(State.DownloadCompleted)
    assert notifications == [("Download completed", "file.zip", "download")]


def test_failed_download_notifies_with_its_reason(
    manager: DownloadManager, notifications: list[Notification]
) -> None:
    download = FakeDownload("file.zip")
    manager.handle_request(download.as_request())
    download.set_interrupt_reason("Network failed")
    download.set_state(State.DownloadInterrupted)
    assert notifications == [("Download failed", "Network failed", "download")]


def test_quit_drops_private_downloads(manager: DownloadManager) -> None:
    private, normal = FakeDownload(), FakeDownload()
    manager.handle_request(private.as_request(), True)
    manager.handle_request(normal.as_request())
    QCoreApplication.instance().aboutToQuit.emit()
    assert listed_downloads(manager) == [normal]
