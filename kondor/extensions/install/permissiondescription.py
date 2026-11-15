from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication, QObject

CONTEXT = "ExtensionPackage"
HOST_LIMIT = 3
ALL_SITES = QT_TRANSLATE_NOOP("ExtensionPackage", "Read and change all websites")
SOME_SITES = QT_TRANSLATE_NOOP("ExtensionPackage", "Read and change pages on %1")
PERMISSION_LINES = (
    (
        "tabs",
        "tab-new",
        QT_TRANSLATE_NOOP("ExtensionPackage", "Open, close and navigate your tabs"),
    ),
    ("downloads", "download", QT_TRANSLATE_NOOP("ExtensionPackage", "Download files")),
    ("notifications", "notifications", QT_TRANSLATE_NOOP("ExtensionPackage", "Show notifications")),
)


class ExtensionPackage(QObject):
    def describe_more_sites(self, listed: str, more: int) -> str:
        #: %1 is a list of sites, %n the number of further sites
        return str(self.tr("%1 and %n more", None, more).replace("%1", listed))


@dataclass
class PatternParts:
    scheme: str = ""
    host: str = ""
    all: bool = False


@dataclass
class SiteAccess:
    is_all: bool = False
    hosts: list[str] = field(default_factory=list)


def translate(text: str) -> str:
    return str(QCoreApplication.translate(CONTEXT, text))


def entry_of(icon: str, text: str) -> dict[str, Any]:
    return {"icon": icon, "text": text}


def parse_pattern(pattern: str) -> PatternParts:
    parts = PatternParts(all=pattern == "<all_urls>")
    scheme_end = pattern.find("://")
    if parts.all or scheme_end < 0:
        return parts
    parts.scheme = pattern[:scheme_end]
    host_start = scheme_end + 3
    host_end = pattern.find("/", host_start)
    parts.host = pattern[host_start:] if host_end < 0 else pattern[host_start:host_end]
    return parts


def grants_all_sites(parts: PatternParts) -> bool:
    return parts.all or (parts.scheme in ("*", "http", "https") and parts.host == "*")


def add_host(access: SiteAccess, host: str) -> None:
    if host and host not in access.hosts:
        access.hosts.append(host)


def is_broad_include(glob: str, parts: PatternParts) -> bool:
    return "://" not in glob or not parts.host or "*" in parts.host


def add_match(access: SiteAccess, match: str) -> None:
    parts = parse_pattern(match)
    if grants_all_sites(parts):
        access.is_all = True
    else:
        add_host(access, parts.host)


def add_include(access: SiteAccess, glob: str) -> None:
    parts = parse_pattern(glob)
    if is_broad_include(glob, parts):
        access.is_all = True
    else:
        add_host(access, parts.host)


def summarize_sites(matches: list[str], includes: list[str]) -> SiteAccess:
    access = SiteAccess()
    for match in matches:
        add_match(access, match)
    for glob in includes:
        add_include(access, glob)
    return access


def host_list(hosts: list[str]) -> str:
    listed = ", ".join(hosts[:HOST_LIMIT])
    if len(hosts) <= HOST_LIMIT:
        return listed
    return ExtensionPackage().describe_more_sites(listed, len(hosts) - HOST_LIMIT)


def site_access_entry(matches: list[str], includes: list[str]) -> dict[str, Any] | None:
    access = summarize_sites(matches, includes)
    if access.is_all:
        return entry_of("internet-services", translate(ALL_SITES))
    if not access.hosts:
        return None
    text = translate(SOME_SITES).replace("%1", host_list(access.hosts))
    return entry_of("internet-services", text)


def permission_entries(
    matches: list[str], permissions: list[str], includes: list[str]
) -> list[dict[str, Any]]:
    site = site_access_entry(matches, includes)
    entries = [site] if site else []
    for permission, icon, text in PERMISSION_LINES:
        if permission in permissions:
            entries.append(entry_of(icon, translate(text)))
    return entries


def permission_lines(matches: list[str], permissions: list[str], includes: list[str]) -> list[str]:
    return [entry["text"] for entry in permission_entries(matches, permissions, includes)]
