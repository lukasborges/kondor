from pathlib import Path

from kondor.app.crash.crashfiles import CrashFiles


def files_in(tmp_path: Path) -> CrashFiles:
    return CrashFiles(tmp_path)


def test_archivesNonEmptyCrashLogWithItsActions(tmp_path: Path) -> None:
    files = files_in(tmp_path)
    files.crash_log.write_text("Fatal Python error: Segmentation fault")
    files.actions_log.write_text("12:00:00 window opened\n")
    files.archive_previous_crash()
    assert files.has_previous_crash()
    assert files.read_previous_actions() == "12:00:00 window opened"
    assert not files.crash_log.exists()


def test_ignoresEmptyCrashLog(tmp_path: Path) -> None:
    files = files_in(tmp_path)
    files.crash_log.write_text("")
    files.archive_previous_crash()
    assert not files.has_previous_crash()


def test_newerCrashReplacesOlderOne(tmp_path: Path) -> None:
    files = files_in(tmp_path)
    files.last_crash_log.write_text("old")
    files.last_actions_log.write_text("old actions")
    files.crash_log.write_text("new")
    files.archive_previous_crash()
    assert files.read_previous_crash() == "new"
    assert files.read_previous_actions() == ""


def test_discardRemovesBothLastFiles(tmp_path: Path) -> None:
    files = files_in(tmp_path)
    files.last_crash_log.write_text("crash")
    files.last_actions_log.write_text("actions")
    files.discard_previous_crash()
    assert not files.last_crash_log.exists()
    assert not files.last_actions_log.exists()
