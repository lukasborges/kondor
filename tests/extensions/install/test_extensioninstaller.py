from pathlib import Path

import pytest

from kondor.extensions.install.extensioninstaller import ExtensionInstaller
from kondor.extensions.package.packagefile import PackageFile
from tests.extensions.extensionsharness import sample_package, write_file


@pytest.fixture
def installer(qapp: object, tmp_path: Path) -> ExtensionInstaller:
    return ExtensionInstaller(str(tmp_path / "extensions"))


def leftovers(installer: ExtensionInstaller) -> list[str]:
    root = Path(installer.extensions_directory)
    return sorted(path.name for path in root.iterdir())


def test_commit_replaces_the_existing_folder(installer: ExtensionInstaller, tmp_path: Path) -> None:
    file = PackageFile(sample_package(str(tmp_path)), "file")
    for _round in range(2):
        staged, error = installer.stage(file)
        assert staged is not None, error
        assert installer.commit(staged) == ""
    assert leftovers(installer) == ["sample"]


def test_failed_stage_leaves_no_staging_folder(
    installer: ExtensionInstaller, tmp_path: Path
) -> None:
    assert write_file(f"{tmp_path}/broken.kondorext", b"not a zip")
    staged, error = installer.stage(PackageFile(f"{tmp_path}/broken.kondorext", "file"))
    assert staged is None
    assert error
    assert leftovers(installer) == []


def test_discard_removes_a_temporary_zip(installer: ExtensionInstaller, tmp_path: Path) -> None:
    path = sample_package(str(tmp_path))
    staged, _error = installer.stage(PackageFile(path, "userscript", "", True))
    assert staged is not None
    installer.discard(staged)
    assert not Path(path).exists()
    assert leftovers(installer) == []
