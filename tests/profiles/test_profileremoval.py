from pathlib import Path

import pytest
from PySide6.QtTest import QTest

from kondor.profiles import profilepaths
from kondor.profiles.profileremoval import remove_profile_data, settings_file
from kondor.profiles.userprofile import DEFAULT_ID
from tests.passwords.fakewallet import FakeWallet

OTHER = "ab12cd34"


@pytest.fixture(autouse=True)
def no_wallet_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KONDOR_NO_KWALLET", raising=False)


def make_profile_files() -> list[Path]:
    paths = [
        profilepaths.data_directory(OTHER),
        *profilepaths.web_data_directories(OTHER),
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        (path / "file").write_text("data")
    settings = settings_file(OTHER)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text("[General]\n")
    return [*paths, settings]


def test_removes_data_web_storage_and_settings() -> None:
    paths = make_profile_files()

    assert remove_profile_data(OTHER, FakeWallet())
    assert [path.exists() for path in paths] == [False] * 4


def test_removes_the_wallet_folder() -> None:
    wallet = FakeWallet()
    wallet.folders[f"Kondor-{OTHER}"] = {"https://a.example": b""}
    wallet.folders["Kondor"] = {}

    remove_profile_data(OTHER, wallet)
    QTest.qWait(50)

    assert list(wallet.folders) == ["Kondor"]


def test_keeps_the_wallet_folder_when_the_wallet_does_not_open() -> None:
    wallet = FakeWallet()
    wallet.can_open = False
    wallet.folders[f"Kondor-{OTHER}"] = {}

    assert remove_profile_data(OTHER, wallet)
    QTest.qWait(50)

    assert f"Kondor-{OTHER}" in wallet.folders


def test_never_removes_default() -> None:
    assert not remove_profile_data(DEFAULT_ID, FakeWallet())
