from pathlib import Path

from PySide6.QtGui import QGuiApplication

from kondor.app.crash.crashfiles import CrashFiles
from kondor.app.crash.crashreporter import CrashReporter

LONG_ACTIONS = "10:00:00 event\n" * 700


def offered(
    tmp_path: Path, actions: str = "10:00:00 window opened"
) -> tuple[CrashReporter, CrashFiles]:
    files = CrashFiles(tmp_path)
    files.last_crash_log.write_text("Fatal Python error: Segmentation fault")
    files.last_actions_log.write_text(actions)
    reporter = CrashReporter()
    reporter.offer(files)
    return reporter, files


def test_barIsClaimedOnlyOnce(tmp_path: Path) -> None:
    reporter, _ = offered(tmp_path)
    assert reporter.claimBar()
    assert not reporter.claimBar()


def test_noBarWithoutPreviousCrash(tmp_path: Path) -> None:
    reporter = CrashReporter()
    reporter.offer(CrashFiles(tmp_path))
    assert not reporter.claimBar()


def test_noBarBeforeRecordingStarts() -> None:
    assert not CrashReporter().claimBar()


def test_reportBuildsIssueAddressAndDeletesFiles(tmp_path: Path) -> None:
    reporter, files = offered(tmp_path)
    address = reporter.report().toString()
    assert address.startswith("https://github.com/lukasborges/kondor-browser/issues/new")
    assert not files.has_previous_crash()


def test_longReportGoesToClipboard(qapp: QGuiApplication, tmp_path: Path) -> None:
    reporter, _ = offered(tmp_path, LONG_ACTIONS)
    reporter.report()
    assert "### Last actions" in QGuiApplication.clipboard().text()


def test_dismissDeletesFiles(tmp_path: Path) -> None:
    reporter, files = offered(tmp_path)
    reporter.dismiss()
    assert not files.last_actions_log.exists()


def test_reportAfterDismissReturnsEmptyAddress(tmp_path: Path) -> None:
    reporter, _ = offered(tmp_path)
    reporter.dismiss()
    assert reporter.report().isEmpty()
