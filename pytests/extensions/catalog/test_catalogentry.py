import json
from typing import Any

import pytest
from PySide6.QtCore import QUrl

from kondor.extensions.catalog.catalogentry import (
    is_newer_version,
    parse_catalog,
    parse_catalog_entry,
)

CATALOG_URL = QUrl("https://example.com/catalog/catalog.json")


def entry_json(**extra: Any) -> dict[str, Any]:
    base = {
        "id": "sample",
        "version": "1.0.0",
        "package": "packages/sample.kondorext",
        "sha256": "ABCDEF",
    }
    return {**base, **extra}


def catalog_bytes(root: dict[str, Any]) -> bytes:
    return json.dumps(root).encode()


def test_resolves_relative_package_and_icon_urls() -> None:
    entry = parse_catalog_entry(entry_json(icon="icons/sample.svg"), CATALOG_URL)
    assert entry is not None
    assert entry.package.toString() == "https://example.com/catalog/packages/sample.kondorext"
    assert entry.icon_source == "https://example.com/catalog/icons/sample.svg"
    assert entry.sha256 == "abcdef"


@pytest.mark.parametrize("missing", ["id", "version", "package"])
def test_skips_entries_without_id_version_or_package(missing: str) -> None:
    broken = entry_json()
    del broken[missing]
    assert parse_catalog_entry(broken, CATALOG_URL) is None
    root = {"version": 1, "extensions": [broken, entry_json()]}
    entries, error = parse_catalog(catalog_bytes(root), CATALOG_URL)
    assert entries is not None
    assert (len(entries), error) == (1, "")


def test_keeps_icon_names_as_they_are() -> None:
    named = parse_catalog_entry(entry_json(icon="dark-mode"), CATALOG_URL)
    none = parse_catalog_entry(entry_json(), CATALOG_URL)
    assert named is not None
    assert none is not None
    assert named.icon_source == "dark-mode"
    assert none.icon_source == "preferences-plugin"


def test_invalid_json_is_refused() -> None:
    entries, error = parse_catalog(b"{nope", CATALOG_URL)
    assert entries is None
    assert error == "The catalog is not valid JSON"


@pytest.mark.parametrize(
    "root",
    [{"version": 2, "extensions": []}, {"version": 1, "extensions": {}}],
    ids=["version-2", "extensions-object"],
)
def test_unsupported_format_is_refused(root: dict[str, Any]) -> None:
    entries, error = parse_catalog(catalog_bytes(root), CATALOG_URL)
    assert entries is None
    assert error == "The catalog has an unsupported format"


@pytest.mark.parametrize(
    ("candidate", "installed", "is_newer"),
    [("1.10.0", "1.9.0", True), ("1.0", "1.0.0", False), ("2.0.0", "2.0.0", False)],
)
def test_compares_versions(candidate: str, installed: str, is_newer: bool) -> None:
    assert is_newer_version(candidate, installed) is is_newer
