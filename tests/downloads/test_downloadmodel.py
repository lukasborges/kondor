from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QLocale

from kondor.downloads import downloadroles
from kondor.downloads.downloaditem import DownloadItem
from kondor.downloads.downloadmodel import DownloadModel
from kondor.downloads.downloadroles import Role
from tests.downloads.fakedownload import FakeDownload, State

HALF_DONE = 0.5
SAVED_SIZE = 5000
REPORTED_SIZE = 700


def in_progress(received: int, total: int) -> FakeDownload:
    download = FakeDownload("file.bin")
    download.set_state(State.DownloadInProgress)
    download.set_bytes(received, total)
    return download


def model_with(*downloads: FakeDownload) -> DownloadModel:
    model = DownloadModel()
    for download in downloads:
        model.add_download(download.as_request(), False)
    return model


def progress_of(model: DownloadModel) -> object:
    return model.data(model.index(0), Role.ProgressRole)


def test_adds_a_download_once(qapp: object) -> None:
    download = FakeDownload()
    model = model_with(download, download)
    assert model.rowCount() == 1
    assert model.property("count") == 1


def test_progress_is_unknown_without_total(qapp: object) -> None:
    assert progress_of(model_with(in_progress(500, 0))) == -1.0


def test_progress_is_capped_at_one(qapp: object) -> None:
    assert progress_of(model_with(in_progress(900, 600))) == 1.0


def test_active_progress_averages_active_downloads(qapp: object) -> None:
    completed = in_progress(10, 100)
    completed.set_state(State.DownloadCompleted)
    model = model_with(in_progress(25, 100), in_progress(75, 100), completed)
    assert model.active_progress() == HALF_DONE
    assert model_with(completed).active_progress() == -1.0


def test_clear_finished_keeps_active_downloads(qapp: object) -> None:
    active, cancelled = in_progress(1, 2), FakeDownload()
    cancelled.set_state(State.DownloadCancelled)
    model = model_with(active, cancelled)
    model.clear_finished()
    assert model.rowCount() == 1
    assert model.download_at(0) is active


def test_removes_private_downloads_only(qapp: object) -> None:
    normal, private = FakeDownload(), FakeDownload()
    model = DownloadModel()
    model.add_download(private.as_request(), True)
    model.add_download(normal.as_request(), False)
    model.remove_private_downloads()
    assert model.rowCount() == 1
    assert model.download_at(0) is normal


def test_destroyed_download_leaves_the_list(qapp: object) -> None:
    download = FakeDownload()
    model = model_with(download)
    download.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert model.rowCount() == 0


def test_speed_text_rounds_half_away_from_zero(qapp: object) -> None:
    item = DownloadItem(None, in_progress(0, 10).as_request())
    item.speed.restart(0)
    item.speed.update(5, 2000)
    expected = f"{QLocale().formattedDataSize(3)}/s"
    assert downloadroles.speed_text_of(item) == expected


def finished_save_page(directory: str, reported_bytes: int) -> FakeDownload:
    download = FakeDownload("page.html", is_save_page=True)
    download.setDownloadDirectory(directory)
    download.set_bytes(reported_bytes, reported_bytes)
    download.set_state(State.DownloadCompleted)
    return download


def received_bytes_of(model: DownloadModel) -> object:
    return model.data(model.index(0), Role.ReceivedBytesRole)


def test_finished_save_page_shows_the_saved_file_size(qapp: object, tmp_path: Path) -> None:
    (tmp_path / "page.html").write_bytes(b"x" * SAVED_SIZE)
    model = model_with(finished_save_page(str(tmp_path), 28))
    assert received_bytes_of(model) == SAVED_SIZE


def test_finished_normal_download_shows_the_reported_size(qapp: object) -> None:
    download = FakeDownload("file.bin")
    download.set_bytes(REPORTED_SIZE, REPORTED_SIZE)
    download.set_state(State.DownloadCompleted)
    assert received_bytes_of(model_with(download)) == REPORTED_SIZE


def test_state_change_refreshes_the_received_bytes(qapp: object) -> None:
    download = in_progress(3, 3)
    model = model_with(download)
    changed_roles: list[list[int]] = []
    model.dataChanged.connect(lambda _top, _bottom, roles: changed_roles.append(list(roles)))
    download.set_state(State.DownloadCompleted)
    assert any(Role.ReceivedBytesRole in roles for roles in changed_roles)
