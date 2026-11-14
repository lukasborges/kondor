from dataclasses import dataclass, field

from PySide6.QtCore import QCoreApplication, QRegularExpression

STRING_FIELDS = {
    "name": "name",
    "namespace": "namespace_name",
    "version": "version",
    "description": "description",
    "author": "author",
    "license": "license",
    "updateURL": "update_url",
    "downloadURL": "download_url",
}
LIST_FIELDS = {
    "match": "matches",
    "include": "includes",
    "exclude": "excludes",
    "exclude-match": "excludes",
    "grant": "grants",
    "require": "required_urls",
}
HOMEPAGE_KEYS = ("homepageURL", "homepage", "website")
SUPPORTED_GRANTS = (
    "none",
    "GM.info",
    "GM_info",
    "GM.getValue",
    "GM.setValue",
    "GM.deleteValue",
    "GM.listValues",
    "GM.addStyle",
    "GM_addStyle",
    "GM.notification",
    "GM_notification",
)
NOTIFICATION_GRANTS = ("GM.notification", "GM_notification")
BLOCK_START = QRegularExpression(r"^\s*//\s*==UserScript==\s*$")
BLOCK_END = QRegularExpression(r"^\s*//\s*==/UserScript==\s*$")
FIELD_LINE = QRegularExpression(r"^\s*//\s*@([\w:.-]+)\s*(.*?)\s*$")


def translated(text: str) -> str:
    return str(QCoreApplication.translate("UserScript", text))


@dataclass
class UserScriptMetadata:
    name: str = ""
    namespace_name: str = ""
    version: str = ""
    description: str = ""
    author: str = ""
    homepage: str = ""
    license: str = ""
    update_url: str = ""
    download_url: str = ""
    run_at: str = "document-idle"
    all_frames: bool = True
    uses_resource: bool = False
    matches: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    grants: list[str] = field(default_factory=list)
    required_urls: list[str] = field(default_factory=list)

    def unsupported_features(self) -> list[str]:
        unsupported = list(dict.fromkeys(g for g in self.grants if g not in SUPPORTED_GRANTS))
        return unsupported + ["@resource"] if self.uses_resource else unsupported

    def wants_notifications(self) -> bool:
        return any(grant in self.grants for grant in NOTIFICATION_GRANTS)


def first_matching_line(lines: list[str], pattern: QRegularExpression, start: int) -> int:
    for index in range(start, len(lines)):
        if pattern.match(lines[index]).hasMatch():
            return index
    return -1


def block_lines(source: str) -> list[str]:
    lines = source.split("\n")
    first = first_matching_line(lines, BLOCK_START, 0)
    if first < 0:
        return []
    last = first_matching_line(lines, BLOCK_END, first)
    return [] if last < 0 else lines[first + 1 : last]


def mapped_run_at(value: str) -> str:
    if value == "document-start":
        return value
    return "document-end" if value in ("document-end", "document-body") else "document-idle"


def apply_special_field(metadata: UserScriptMetadata, key: str, value: str) -> None:
    if key in HOMEPAGE_KEYS and not metadata.homepage:
        metadata.homepage = value
    elif key == "run-at":
        metadata.run_at = mapped_run_at(value)
    elif key == "noframes":
        metadata.all_frames = False
    elif key == "resource":
        metadata.uses_resource = True


def apply_field(metadata: UserScriptMetadata, key: str, value: str) -> None:
    if key in STRING_FIELDS:
        if not getattr(metadata, STRING_FIELDS[key]):
            setattr(metadata, STRING_FIELDS[key], value)
    elif key in LIST_FIELDS:
        getattr(metadata, LIST_FIELDS[key]).append(value)
    else:
        apply_special_field(metadata, key, value)


def metadata_from(lines: list[str]) -> UserScriptMetadata:
    metadata = UserScriptMetadata()
    for line in lines:
        match = FIELD_LINE.match(line)
        if match.hasMatch():
            apply_field(metadata, match.captured(1), match.captured(2))
    return metadata


def problem_of(lines: list[str], metadata: UserScriptMetadata) -> str:
    if not lines:
        return translated("The script has no metadata block")
    if not metadata.name:
        return translated("The script has no @name")
    if not metadata.matches and not metadata.includes:
        return translated("The script has neither @match nor @include")
    return ""


def parse_user_script_metadata(source: str) -> tuple[UserScriptMetadata | None, str]:
    lines = block_lines(source)
    metadata = metadata_from(lines)
    error = problem_of(lines, metadata)
    return (None, error) if error else (metadata, "")
