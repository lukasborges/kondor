from typing import Any

from kondor.extensions.manifest.jsonvalue import UNDEFINED, to_bool, to_string, value_of
from kondor.extensions.manifest.manifestsections import manifest_error
from kondor.extensions.manifest.stringlistfield import StringListField, read_string_list
from kondor.extensions.package.contentscript import ExtensionContentScript
from kondor.extensions.package.packagepath import package_file_error

KNOWN_RUN_AT_VALUES = ("document-start", "document-end", "document-idle")
LIST_KEYS = ("matches", "include", "exclude", "js", "css")


class ContentScriptReader:
    def __init__(self, directory: str, where: str) -> None:
        self.directory = directory
        self.where = where
        self.message = ""

    def error(self) -> str:
        return self.message

    def read(self, source: dict[str, Any]) -> ExtensionContentScript | None:
        script = ExtensionContentScript()
        if not self.read_lists(source, script) or not self.check_lists(script):
            return None
        if not self.read_run_at(source, script):
            return None
        script.all_frames = to_bool(source.get("allFrames"))
        return script

    def read_lists(self, source: dict[str, Any], script: ExtensionContentScript) -> bool:
        for key in LIST_KEYS:
            values, self.message = read_string_list(source, StringListField(key, self.where))
            if values is None:
                return False
            setattr(script, key, values)
        return True

    def check_lists(self, script: ExtensionContentScript) -> bool:
        if not script.matches and not script.include:
            return self.fail(f"{self.where}.matches: must not be empty")
        if not script.js and not script.css:
            return self.fail(f"{self.where}: needs at least one js or css file")
        return self.check_files(script.js, ".js") and self.check_files(script.css, ".css")

    def check_files(self, files: list[str], kind: str) -> bool:
        for file in files:
            self.message = package_file_error(self.directory, file, self.where + kind)
            if self.message:
                return False
        return True

    def read_run_at(self, source: dict[str, Any], script: ExtensionContentScript) -> bool:
        run_at = value_of(source, "runAt")
        if run_at is UNDEFINED:
            return True
        if to_string(run_at) not in KNOWN_RUN_AT_VALUES:
            return self.fail(
                f"{self.where}.runAt: must be document-start, document-end or document-idle"
            )
        script.run_at = to_string(run_at)
        return True

    def fail(self, message: str) -> bool:
        self.message = manifest_error(message)
        return False
