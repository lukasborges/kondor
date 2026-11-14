from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from kondor.passwords.passwordstore import PasswordStore
from kondor.passwords.wallet.walletfolder import FOLDER
from kondor.passwords.wallet.walletmap import map_from_bytes
from pytests.passwords.fakewallet import FakeWallet

SITE = "https://example.com"
TWO_OPEN_REQUESTS = 2
CSV = "url,username,password\nhttps://a.example,ann,pw1\nhttps://b.example,bob,pw2\n"


def open_store(store: PasswordStore, qtbot: QtBot) -> None:
    store.ensureOpen()
    qtbot.waitUntil(lambda: store.state != "opening")


def test_opens_through_opening_to_open(
    store: PasswordStore, wallet: FakeWallet, qtbot: QtBot
) -> None:
    store.ensureOpen()
    assert store.state == "opening"
    qtbot.waitUntil(lambda: store.state == "open")
    assert FOLDER in wallet.folders


def test_disabled_by_environment_is_unavailable(
    store: PasswordStore, wallet: FakeWallet, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KONDOR_NO_KWALLET", "1")
    store.ensureOpen()
    assert store.state == "unavailable"
    assert wallet.open_requests == 0


def test_failed_open_is_unavailable(store: PasswordStore, wallet: FakeWallet, qtbot: QtBot) -> None:
    wallet.can_open = False
    open_store(store, qtbot)
    assert store.state == "unavailable"


def test_folder_that_cannot_be_created_is_unavailable(
    store: PasswordStore, wallet: FakeWallet, qtbot: QtBot
) -> None:
    wallet.can_create_folder = False
    open_store(store, qtbot)
    assert store.state == "unavailable"


def test_save_lists_the_entry_and_reads_the_password(store: PasswordStore, qtbot: QtBot) -> None:
    open_store(store, qtbot)
    with qtbot.waitSignal(store.changed):
        assert store.save(SITE, "bob", "pw-b")
    store.save(SITE, "Ann", "pw-a")
    assert {"origin": SITE, "host": "example.com", "username": "bob"} in store.entries
    assert store.contains(SITE, "bob")
    assert store.usernames(SITE) == ["Ann", "bob"]
    assert store.password(SITE, "bob") == "pw-b"


def test_save_is_refused_when_closed_or_without_origin(store: PasswordStore, qtbot: QtBot) -> None:
    assert not store.save(SITE, "bob", "pw")
    open_store(store, qtbot)
    assert not store.save("", "bob", "pw")
    assert store.entries == []


def test_save_reports_a_failed_write(
    store: PasswordStore, wallet: FakeWallet, qtbot: QtBot
) -> None:
    open_store(store, qtbot)
    wallet.can_write = False
    assert not store.save(SITE, "bob", "pw")
    assert not store.contains(SITE, "bob")


def test_remove_last_login_removes_the_entry(
    store: PasswordStore, wallet: FakeWallet, qtbot: QtBot
) -> None:
    open_store(store, qtbot)
    store.save(SITE, "bob", "pw")
    store.remove(SITE, "bob")
    assert SITE not in wallet.folders[FOLDER]
    assert store.entries == []


def test_saved_bytes_are_kwallet_maps(
    store: PasswordStore, wallet: FakeWallet, qtbot: QtBot
) -> None:
    open_store(store, qtbot)
    store.save(SITE, "bob", "pw-b")
    store.save(SITE, "ann", "pw-a")
    assert map_from_bytes(wallet.folders[FOLDER][SITE]) == {"ann": "pw-a", "bob": "pw-b"}


def test_closed_wallet_forgets_the_logins(
    store: PasswordStore, wallet: FakeWallet, qtbot: QtBot
) -> None:
    open_store(store, qtbot)
    store.save(SITE, "bob", "pw")
    wallet.close()
    assert store.state == "closed"
    assert store.entries == []


def test_retry_after_unavailable_opens_again(
    store: PasswordStore, wallet: FakeWallet, qtbot: QtBot
) -> None:
    wallet.can_open = False
    open_store(store, qtbot)
    wallet.can_open = True
    store.retry()
    qtbot.waitUntil(lambda: store.state == "open")
    assert wallet.open_requests == TWO_OPEN_REQUESTS


def test_credentials_for_needs_a_cached_origin(store: PasswordStore, qtbot: QtBot) -> None:
    open_store(store, qtbot)
    store.save(SITE, "bob", "pw-b")
    store.save(SITE, "ann", "pw-a")
    assert store.credentials_for("https://other.example") == []
    assert store.credentials_for(SITE) == [
        {"username": "ann", "password": "pw-a"},
        {"username": "bob", "password": "pw-b"},
    ]


def test_import_commit_writes_through_the_wallet(
    store: PasswordStore, qtbot: QtBot, tmp_path: Path
) -> None:
    open_store(store, qtbot)
    file = tmp_path / "logins.csv"
    file.write_text(CSV)
    with qtbot.waitSignal(store.importPrepared):
        store.prepareImport(QUrl.fromLocalFile(str(file)))
    with qtbot.waitSignal(store.importFinished) as finished:
        store.commitImport(False)
    assert finished.args == [2]
    assert [entry["username"] for entry in store.entries] == ["ann", "bob"]
    assert not store.importRunning


def test_prepare_import_without_wallet_fails_at_once(store: PasswordStore, qtbot: QtBot) -> None:
    prepared: list[dict[str, object]] = []
    store.importPrepared.connect(prepared.append)
    store.prepareImport(QUrl.fromLocalFile("/tmp/logins.csv"))
    assert prepared[0]["error"] == "walletUnavailable"
