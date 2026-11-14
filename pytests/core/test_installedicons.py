from pathlib import Path

import pytest

from kondor.core.installedicons import ICON_FOLDER, InstalledIcons

ICON_NAME = "kondor-sample-symbolic"


def test_finds_icon_in_data_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = tmp_path / ICON_FOLDER
    folder.mkdir(parents=True)
    (folder / f"{ICON_NAME}.svg").write_text("<svg/>")
    monkeypatch.setenv("XDG_DATA_DIRS", str(tmp_path))
    assert InstalledIcons.instance().isInstalled(ICON_NAME)


def test_misses_icon_outside_data_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_DATA_DIRS", str(tmp_path))
    assert not InstalledIcons.instance().isInstalled(ICON_NAME)
