from pathlib import Path

import pytest

from kondor.app.startup import stagedbuild


@pytest.fixture
def package_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(stagedbuild, "package_parent_directory", lambda: tmp_path)
    return tmp_path


def test_uses_the_install_folder_when_it_holds_the_resources(package_parent: Path) -> None:
    (package_parent / "kondor.rcc").touch()

    assert stagedbuild.staged_build_directory() == package_parent


def test_uses_the_checkout_build_folder_otherwise(package_parent: Path) -> None:
    assert stagedbuild.staged_build_directory() == package_parent.parent / "build" / "python"
