from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.passwords.csvimport.importtypes import Login
from kondor.passwords.csvimport.passwordimportplan import SavedLogins
from kondor.passwords.importing.importcommit import ImportCommit
from kondor.passwords.importing.importpreparation import ImportPreparation
from kondor.passwords.importing.pendingimport import PendingImport

SITE_A = "https://a.example"
SITE_B = "https://b.example"
CSV = "url,username,password\nhttps://a.example,ann,pw1\nhttps://b.example,bob,pw2\n"
QUIET_MS = 300
TWO_ORIGINS = 2
THREE_LOGINS = 3
TWO_NEW_LOGINS = 2


def two_sites() -> PendingImport:
    return PendingImport([Login(SITE_A, "ann", "pw1"), Login(SITE_B, "bob", "pw2"),
                          Login(SITE_B, "cy", "pw3")])


def always(is_written: bool) -> ImportCommit:
    return ImportCommit(two_sites(), lambda origin, logins: is_written)


def empty_wallet() -> SavedLogins | None:
    return {}


def no_wallet() -> SavedLogins | None:
    return None


@pytest.fixture
def csv_file(tmp_path: Path) -> QUrl:
    file = tmp_path / "logins.csv"
    file.write_text(CSV)
    return QUrl.fromLocalFile(str(file))


def test_reports_progress_per_origin(qtbot: QtBot) -> None:
    commit = always(True)
    progressed: list[None] = []
    commit.progressed.connect(lambda: progressed.append(None))
    assert commit.total() == TWO_ORIGINS
    with qtbot.waitSignal(commit.finished):
        commit.start()
        assert commit.done() == 0
    assert len(progressed) == TWO_ORIGINS
    assert commit.done() == TWO_ORIGINS


def test_counts_written_logins(qtbot: QtBot) -> None:
    commit = always(True)
    with qtbot.waitSignal(commit.finished) as finished:
        commit.start()
    assert finished.args == [THREE_LOGINS]


def test_fails_when_the_wallet_rejects_a_write(qtbot: QtBot) -> None:
    commit = always(False)
    with qtbot.waitSignal(commit.finished) as finished:
        commit.start()
    assert finished.args == [-1]


def test_writes_nothing_for_identical_logins(qtbot: QtBot) -> None:
    pending = PendingImport([Login(SITE_A, "ann", "pw1")], {SITE_A: {"ann": "pw1"}})
    writes: list[str] = []
    commit = ImportCommit(pending, lambda origin, logins: writes.append(origin) is None)
    with qtbot.waitSignal(commit.finished) as finished:
        commit.start()
    assert writes == []
    assert finished.args == [0]


def test_prepare_returns_before_the_file_is_parsed(qtbot: QtBot, csv_file: QUrl) -> None:
    preparation = ImportPreparation(empty_wallet)
    with qtbot.waitSignal(preparation.prepared):
        with qtbot.assertNotEmitted(preparation.prepared, wait=0):
            preparation.start(csv_file)
        assert preparation.is_running()
    assert not preparation.is_running()


def test_prepare_describes_the_file(qtbot: QtBot, csv_file: QUrl) -> None:
    preparation = ImportPreparation(empty_wallet)
    with qtbot.waitSignal(preparation.prepared) as prepared:
        preparation.start(csv_file)
    info = prepared.args[0]
    assert info["error"] == ""
    assert info["newCount"] == TWO_NEW_LOGINS
    assert len(preparation.take_pending().logins) == TWO_NEW_LOGINS


def test_prepare_fails_when_the_wallet_is_unavailable(qtbot: QtBot, csv_file: QUrl) -> None:
    preparation = ImportPreparation(no_wallet)
    with qtbot.waitSignal(preparation.prepared) as prepared:
        preparation.start(csv_file)
    assert prepared.args[0]["error"] == "walletUnavailable"
    assert preparation.take_pending().logins == []


def test_cancel_drops_the_prepared_logins(qtbot: QtBot, csv_file: QUrl) -> None:
    preparation = ImportPreparation(empty_wallet)
    with qtbot.waitSignal(preparation.prepared):
        preparation.start(csv_file)
    preparation.cancel()
    assert preparation.take_pending().logins == []


def test_cancel_while_reading_emits_nothing(qtbot: QtBot, csv_file: QUrl) -> None:
    preparation = ImportPreparation(empty_wallet)
    with qtbot.assertNotEmitted(preparation.prepared, wait=QUIET_MS):
        preparation.start(csv_file)
        preparation.cancel()
    assert not preparation.is_running()
