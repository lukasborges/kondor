from pathlib import Path

import pytest

from kondor.extensions.userscripts.userscriptmetadata import (
    UserScriptMetadata,
    parse_user_script_metadata,
)
from kondor.extensions.userscripts.userscriptversion import (
    is_newer_user_script_version,
    normalized_user_script_version,
)

FIXTURES = Path(__file__).resolve().parent.parent.parent / "data" / "userscripts"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def parsed(source: str) -> UserScriptMetadata:
    metadata, _error = parse_user_script_metadata(source)
    return metadata or UserScriptMetadata()


def script_with(line: str) -> str:
    return f"// ==UserScript==\n// @name N\n// @match *://*/*\n{line}\n// ==/UserScript==\n"


def test_reads_every_key() -> None:
    metadata = parsed(fixture("wide.user.js"))
    assert metadata.name == "Wide Test"
    assert metadata.namespace_name == "test"
    assert metadata.version == "1.0"
    assert metadata.author == "Jane Example"
    assert metadata.homepage == "https://example.org/wide"
    assert metadata.license == "MIT"
    assert metadata.matches == ["*://127.0.0.1/*"]
    assert metadata.includes == ["https://*.example.org/*"]
    assert metadata.excludes == ["*://127.0.0.1/excluded/*"]
    assert metadata.required_urls == ["lib.js"]
    assert metadata.update_url == "https://example.org/wide.meta.js"
    assert metadata.download_url == "https://example.org/wide.user.js"
    assert not metadata.all_frames
    assert metadata.wants_notifications()


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("// @run-at document-start", "document-start"),
        ("// @run-at document-end", "document-end"),
        ("// @run-at document-body", "document-end"),
        ("// @run-at document-idle", "document-idle"),
        ("// @run-at context-menu", "document-idle"),
        ("", "document-idle"),
    ],
    ids=["start", "end", "body", "idle", "unknown", "absent"],
)
def test_maps_run_at(line: str, expected: str) -> None:
    assert parsed(script_with(line)).run_at == expected


@pytest.mark.parametrize("name", ["no-block.user.js", "no-name.user.js", "no-match.user.js"])
def test_refuses_invalid_scripts(name: str) -> None:
    source = fixture(name)
    assert source
    metadata, error = parse_user_script_metadata(source)
    assert metadata is None
    assert error


def test_lists_unsupported_features_in_file_order() -> None:
    metadata = parsed(fixture("wide.user.js"))
    assert metadata.unsupported_features() == ["GM_xmlhttpRequest", "@resource"]


def test_takes_the_first_homepage_key() -> None:
    source = script_with("// @website https://a.example\n// @homepage https://b.example")
    assert parsed(source).homepage == "https://a.example"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.2", "1.2.0"),
        ("0.3.1b", "0.3.1"),
        ("2024.05.01.2", "2024.5.1"),
        ("", "0.0.0"),
        ("beta", "0.0.0"),
    ],
    ids=["two parts", "suffix", "four parts", "absent", "text"],
)
def test_normalizes_versions(raw: str, expected: str) -> None:
    assert normalized_user_script_version(raw) == expected


@pytest.mark.parametrize(
    ("candidate", "installed", "is_newer"),
    [
        ("1.10", "1.9", True),
        ("1.2", "1.2.0", False),
        ("1.1", "1.2", False),
        ("1.2.0.1", "1.2", True),
        ("1.0b", "1.0", True),
    ],
    ids=["greater", "equal", "older", "longer", "suffix"],
)
def test_compares_versions(candidate: str, installed: str, is_newer: bool) -> None:
    assert is_newer_user_script_version(candidate, installed) is is_newer
