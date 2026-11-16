import os
from pathlib import Path

import pytest

from kondor.app.startup import environment

DICTIONARIES = environment.DICTIONARIES_VARIABLE
PORTAL = environment.PORTAL_VARIABLE


@pytest.fixture
def staged(tmp_path: Path) -> Path:
    staged = tmp_path / "build" / "python"
    staged.mkdir(parents=True)
    return staged


def test_picks_the_first_existing_dictionary_candidate(
    staged: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(DICTIONARIES, raising=False)
    (staged / "qtwebengine_dictionaries").mkdir()
    (staged.parent / "share" / "kondor" / "qtwebengine_dictionaries").mkdir(parents=True)

    environment.find_dictionaries(str(staged))

    expected = staged.parent / "share" / "kondor" / "qtwebengine_dictionaries"
    assert Path(os.environ[DICTIONARIES]) == expected


def test_keeps_an_already_set_dictionary_variable(
    staged: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(DICTIONARIES, "/already/set")
    (staged / "qtwebengine_dictionaries").mkdir()

    environment.find_dictionaries(str(staged))

    assert os.environ[DICTIONARIES] == "/already/set"


def test_sets_nothing_without_candidates(staged: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DICTIONARIES, raising=False)

    environment.find_dictionaries(str(staged))

    assert DICTIONARIES not in os.environ


def test_app_image_enables_the_portal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APPIMAGE", "/tmp/kondor.AppImage")
    monkeypatch.delenv(PORTAL, raising=False)

    environment.use_portal_inside_app_image()

    assert os.environ[PORTAL] == "1"


def test_portal_is_left_alone_outside_an_app_image(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APPIMAGE", raising=False)
    monkeypatch.delenv(PORTAL, raising=False)

    environment.use_portal_inside_app_image()

    assert PORTAL not in os.environ


def test_portal_keeps_an_already_set_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APPIMAGE", "/tmp/kondor.AppImage")
    monkeypatch.setenv(PORTAL, "0")

    environment.use_portal_inside_app_image()

    assert os.environ[PORTAL] == "0"


FLAGS = environment.CHROMIUM_FLAGS_VARIABLE


def test_disables_the_chromium_media_player_when_no_flags_are_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(FLAGS, raising=False)

    environment.turn_off_chromium_media_player()

    assert os.environ[FLAGS] == "--disable-features=HardwareMediaKeyHandling"


def test_appends_to_an_existing_disable_features_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAGS, "--disable-features=Foo")

    environment.turn_off_chromium_media_player()

    assert os.environ[FLAGS] == "--disable-features=Foo,HardwareMediaKeyHandling"


def test_keeps_other_chromium_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FLAGS, "--foo --bar=1")

    environment.turn_off_chromium_media_player()

    assert os.environ[FLAGS] == "--foo --bar=1 --disable-features=HardwareMediaKeyHandling"
