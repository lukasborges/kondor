import zipfile
from pathlib import Path

import pytest

from kondor.extensions.package.extensionpackage import ExtensionPackage
from pytests.extensions.extensionsharness import (
    data_dir,
    make_variant,
    write_file,
    zip_directory,
)

INVALID_FIXTURES = {
    "missing file": (
        "missing-file",
        "manifest.json: contentScripts[0].js: file not found: content.js",
    ),
    "bad id": ("bad-id", "manifest.json: id: must match ^[a-z0-9][a-z0-9-]{1,47}$"),
    "dot dot": ("dotdot", "manifest.json: contentScripts[0].js: invalid path: ../secret.js"),
    "no manifest": ("does-not-exist", "manifest.json: file not found"),
}


@pytest.fixture(autouse=True)
def application(qapp: object) -> None:
    return None


def load_sample() -> ExtensionPackage:
    package, error = ExtensionPackage.load(data_dir("sample"))
    assert package.is_valid(), error
    return package


def test_valid_sample() -> None:
    package = load_sample()
    assert package.id() == "sample"
    assert package.version() == "1.0.0"
    assert package.permissions() == ["tabs", "notifications"]
    assert len(package.content_scripts()) == 1
    assert package.content_scripts()[0].run_at == "document-end"
    assert package.has_settings()
    assert package.has_action()
    assert package.action_site_toggle()
    assert package.icon_source().startswith("file://")
    assert package.setting_defaults()["greeting"] == "hello"


@pytest.mark.parametrize(("fixture", "message"), INVALID_FIXTURES.values(), ids=INVALID_FIXTURES)
def test_invalid_fixtures(fixture: str, message: str) -> None:
    package, error = ExtensionPackage.load(data_dir(fixture))
    assert not package.is_valid()
    assert error == message


def test_too_many_files(tmp_path: Path) -> None:
    directory = make_variant(str(tmp_path), "many", lambda manifest: None)
    for index in range(ExtensionPackage.MAX_PACKAGE_FILES):
        assert write_file(f"{directory}/extra/f{index}.txt", b"x")
    package, error = ExtensionPackage.load(directory)
    assert not package.is_valid()
    assert "200 files" in error


def test_too_large_package(tmp_path: Path) -> None:
    directory = make_variant(str(tmp_path), "large", lambda manifest: None)
    assert write_file(f"{directory}/big.bin", b"x" * (ExtensionPackage.MAX_PACKAGE_BYTES + 1))
    package, error = ExtensionPackage.load(directory)
    assert not package.is_valid()
    assert "larger than 5 MiB" in error


def test_too_large_archive(tmp_path: Path) -> None:
    directory = make_variant(str(tmp_path), "largezip", lambda manifest: None)
    assert write_file(f"{directory}/big.bin", b"x" * (ExtensionPackage.MAX_PACKAGE_BYTES + 1))
    zip_path = str(tmp_path / "large.kondorext")
    assert zip_directory(directory, zip_path)
    target = tmp_path / "unpacked-large"
    assert "larger than 5 MiB" in ExtensionPackage.unpack(zip_path, str(target))
    assert not (target / "big.bin").exists()


def test_unsafe_archive_entry(tmp_path: Path) -> None:
    zip_path = tmp_path / "unsafe.kondorext"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("manifest.json", b"{}")
        archive.writestr("../evil.js", b"x")
    error = ExtensionPackage.unpack(str(zip_path), str(tmp_path / "unpacked-unsafe"))
    assert "Unsafe file name" in error
    assert not (tmp_path / "evil.js").exists()


def test_localized_strings() -> None:
    package = load_sample()
    assert package.name("pt_BR") == "Extensão de Exemplo"
    assert package.name("pt_PT") == "Sample Extension"
    assert package.name("de") == "Sample Extension"
    assert package.settings_schema("pt_BR")[0]["label"] == "Saudação"
    assert package.action_items("pt_BR")[0]["title"] == "Alternar Marca"


def test_permission_lines_for_sites() -> None:
    lines = ExtensionPackage.permission_lines
    assert lines(["https://*/*", "http://*/*"], []) == ["Read and change all websites"]
    assert len(lines(["<all_urls>"], [])) == 1
    assert lines(["*://www.youtube.com/*"], []) == ["Read and change pages on www.youtube.com"]
    many = [f"https://{letter}.com/*" for letter in "abcde"]
    assert lines(many, [])[0] == "Read and change pages on a.com, b.com, c.com and 2 more"


def test_permission_lines_for_capabilities() -> None:
    permissions = ["tabs", "downloads", "notifications"]
    lines = ExtensionPackage.permission_lines(["<all_urls>"], permissions)
    assert lines[0].startswith("Read and change")
    assert lines[1:] == [
        "Open, close and navigate your tabs",
        "Download files",
        "Show notifications",
    ]
