import stat
import zipfile
from pathlib import Path

import pytest

from kondor.extensions.package.packagearchive import unpack


@pytest.fixture(autouse=True)
def application(qapp: object) -> None:
    return None


def make_zip(path: Path, entries: dict[str, bytes]) -> str:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return str(path)


def add_link(path: Path, name: str, target: str) -> None:
    info = zipfile.ZipInfo(name)
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr(info, target)


def test_rejects_an_absolute_entry(tmp_path: Path) -> None:
    zip_path = make_zip(tmp_path / "a.zip", {"/etc/evil": b"x"})
    assert "Unsafe file name in the package: /etc/evil" in unpack(zip_path, str(tmp_path / "out"))
    assert not (tmp_path / "out").exists()


def test_skips_symbolic_links(tmp_path: Path) -> None:
    zip_path = make_zip(tmp_path / "a.zip", {"real.txt": b"x"})
    add_link(tmp_path / "a.zip", "link.txt", "real.txt")
    assert unpack(zip_path, str(tmp_path / "out")) == ""
    assert (tmp_path / "out" / "real.txt").exists()
    assert not (tmp_path / "out" / "link.txt").exists()


def test_writes_nested_files(tmp_path: Path) -> None:
    zip_path = make_zip(tmp_path / "a.zip", {"a/b/c.txt": b"deep", "top.txt": b"top"})
    assert unpack(zip_path, str(tmp_path / "out")) == ""
    assert (tmp_path / "out" / "a" / "b" / "c.txt").read_bytes() == b"deep"
    assert (tmp_path / "out" / "top.txt").read_bytes() == b"top"


def test_not_a_zip_is_refused(tmp_path: Path) -> None:
    not_a_zip = tmp_path / "plain.kondorext"
    not_a_zip.write_bytes(b"plain text")
    assert unpack(str(not_a_zip), str(tmp_path / "out")) == "The file is not a valid ZIP archive"
