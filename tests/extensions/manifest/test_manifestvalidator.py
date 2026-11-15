from pathlib import Path
from typing import Any

import pytest
from PySide6.QtGui import QImage

from kondor.extensions.manifest.manifestvalidator import ManifestValidator

ALL_FRAMES = "allFrames"
KEYS_MESSAGE = "manifest.json: action.items[0].keysSetting: must name a keys setting"


def base_manifest() -> dict[str, Any]:
    return {"kondor": 1, "id": "sample-test", "name": "Sample", "version": "1.0.0"}


def script_with(key: str, value: Any) -> dict[str, Any]:
    script: dict[str, Any] = {"matches": ["*://a/*"], "js": ["a.js"]}
    script[key] = value
    return script


def with_scripts(script: dict[str, Any]) -> dict[str, Any]:
    return {**base_manifest(), "contentScripts": [script]}


def with_key(key: str, value: Any) -> dict[str, Any]:
    return {**base_manifest(), key: value}


def without_key(key: str) -> dict[str, Any]:
    manifest = base_manifest()
    del manifest[key]
    return manifest


def with_keys_setting(setting_type: str, reference: str) -> dict[str, Any]:
    setting = {"key": "faster", "type": setting_type, "label": "Faster"}
    item = {"id": "go", "title": "Go", "keysSetting": reference}
    manifest = with_key("settings", [setting])
    manifest["action"] = {"items": [item]}
    return manifest


IDENTITY_ROWS = {
    "no api": (without_key("kondor"), "manifest.json: kondor: required"),
    "api 2": (
        with_key("kondor", 2),
        "manifest.json: kondor: unsupported API version (must be 1)",
    ),
    "no name": (without_key("name"), "manifest.json: name: required, must be a string"),
    "author": (with_key("author", 3), "manifest.json: author: must be a string"),
    "id": (
        with_key("id", "A"),
        "manifest.json: id: must match ^[a-z0-9][a-z0-9-]{1,47}$",
    ),
    "version": (with_key("version", "1"), "manifest.json: version: must be MAJOR.MINOR.PATCH"),
}

CONTENT_ROWS = {
    "permissions": (
        with_key("permissions", 1),
        "manifest.json: permissions: must be a list of strings",
    ),
    "permission": (
        with_key("permissions", ["root"]),
        "manifest.json: permissions: unknown permission: root",
    ),
    "scripts": (with_key("contentScripts", 1), "manifest.json: contentScripts: must be a list"),
    "script": (
        with_key("contentScripts", [1]),
        "manifest.json: contentScripts[0]: must be an object",
    ),
    "matches": (
        with_scripts(script_with("matches", [])),
        "manifest.json: contentScripts[0].matches: must not be empty",
    ),
    "js": (
        with_scripts(script_with("js", ["b.js"])),
        "manifest.json: contentScripts[0].js: file not found: b.js",
    ),
    "runAt": (
        with_scripts(script_with("runAt", "now")),
        "manifest.json: contentScripts[0].runAt: "
        "must be document-start, document-end or document-idle",
    ),
}

SECTION_ROWS = {
    "settings": (with_key("settings", 1), "manifest.json: settings: must be a list"),
    "setting key": (
        with_key("settings", [{}]),
        "manifest.json: settings[0].key: required and unique",
    ),
    "action": (with_key("action", 1), "manifest.json: action: must be an object"),
    "icon": (
        with_key("icon", "small.png"),
        "manifest.json: icon: a PNG icon must be at least 64 px: small.png",
    ),
    "keysSetting unknown": (with_keys_setting("keys", "slower"), KEYS_MESSAGE),
    "keysSetting not keys": (with_keys_setting("bool", "faster"), KEYS_MESSAGE),
}

ROWS = {**IDENTITY_ROWS, **CONTENT_ROWS, **SECTION_ROWS}


@pytest.fixture
def directory(qapp: object, tmp_path: Path) -> Path:
    (tmp_path / "a.js").write_bytes(b"")
    assert QImage(10, 10, QImage.Format.Format_ARGB32).save(str(tmp_path / "small.png"))
    return tmp_path


def test_accepts_the_base_manifest(directory: Path) -> None:
    validator = ManifestValidator(str(directory))
    valid = validator.validate(with_scripts(script_with(ALL_FRAMES, True)))
    assert valid is not None, validator.error()
    assert len(valid.content_scripts) == 1
    assert valid.icon_source == "preferences-plugin"


def test_accepts_keys_setting_of_keys_type(directory: Path) -> None:
    validator = ManifestValidator(str(directory))
    assert validator.validate(with_keys_setting("keys", "faster")) is not None, validator.error()


@pytest.mark.parametrize(("manifest", "message"), ROWS.values(), ids=ROWS.keys())
def test_reports_the_first_error_with_todays_text(
    directory: Path, manifest: dict[str, Any], message: str
) -> None:
    validator = ManifestValidator(str(directory))
    assert validator.validate(manifest) is None
    assert validator.error() == message
