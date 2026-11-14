import json
from pathlib import Path

from kondor.extensions.package.extensionpackage import ExtensionPackage
from kondor.extensions.scripts.contentscriptbuilder import (
    ContentScriptContext,
    content_script_source,
)
from pytests.extensions.extensionsharness import data_dir, write_file

CSS_ONLY_MANIFEST = {
    "kondor": 1,
    "id": "css-only",
    "name": "Css",
    "version": "1.0.0",
    "contentScripts": [{"matches": ["*://a/*"], "css": ["style.css"]}],
}


def context_of(package: ExtensionPackage) -> ContentScriptContext:
    return ContentScriptContext(
        package, 0, "@TOKEN@", "en", True, package.setting_defaults(), ["https://example.com"]
    )


def test_source_matches_the_recorded_script(qapp: object, staged_resources: None) -> None:
    package, error = ExtensionPackage.load(data_dir("sample"))
    assert not error
    recorded = (Path(data_dir("sample")).parent / "sample-content-script.js").read_text()
    assert content_script_source(context_of(package)) == recorded


def test_css_only_script_has_no_java_script_block(
    qapp: object, staged_resources: None, tmp_path: Path
) -> None:
    assert write_file(f"{tmp_path}/style.css", b"body { color: red; }")
    assert write_file(f"{tmp_path}/manifest.json", json.dumps(CSS_ONLY_MANIFEST).encode())
    package, error = ExtensionPackage.load(str(tmp_path))
    assert not error
    source = content_script_source(context_of(package))
    assert "body { color: red; }" in source
    assert "(function (kondor) {" not in source
