from typing import NamedTuple


class ResourceEntry(NamedTuple):
    resource_path: str
    source_path: str


class ResourceGroup(NamedTuple):
    prefix: str
    base: str
    files: tuple[str, ...]


RESOURCE_GROUPS = (
    ResourceGroup("/", "", ("packaging/kondor.png", "packaging/kondor.svg")),
    ResourceGroup(
        "/reader",
        "3rdparty/readability",
        (
            "3rdparty/readability/Readability.js",
            "3rdparty/readability/Readability-readerable.js",
            "3rdparty/readability/template.html",
        ),
    ),
    ResourceGroup(
        "/scripts",
        "src/kondor/passwords/bridge",
        (
            "src/kondor/passwords/bridge/passwords.js",
            "src/kondor/passwords/bridge/usernamefield.js",
        ),
    ),
    ResourceGroup(
        "/scripts",
        "src/kondor/extensions/bridge",
        (
            "src/kondor/extensions/bridge/channel.js",
            "src/kondor/extensions/bridge/extensionruntime.js",
        ),
    ),
    ResourceGroup(
        "/scripts", "src/kondor/extensions/scripts", ("src/kondor/extensions/scripts/usergm.js",)
    ),
    ResourceGroup(
        "/scripts",
        "src/kondor/browser/media",
        (
            "src/kondor/browser/media/mediasession.js",
            "src/kondor/browser/media/mediawatch.js",
        ),
    ),
    ResourceGroup(
        "/mpris",
        "src/kondor/app/mpris",
        ("src/kondor/app/mpris/mprisintrospection.xml",),
    ),
    ResourceGroup(
        "/icons",
        "assets/icons/hicolor/scalable/actions",
        ("assets/icons/hicolor/scalable/actions/kondor-extensions-symbolic.svg",),
    ),
    ResourceGroup("/", "", ("LICENSE",)),
)


def relative_to_base(group: ResourceGroup, source_path: str) -> str:
    if not group.base:
        return source_path
    return source_path.removeprefix(group.base + "/")


def entries_of(group: ResourceGroup) -> list[ResourceEntry]:
    prefix = group.prefix.rstrip("/")
    return [
        ResourceEntry(f"{prefix}/{relative_to_base(group, source)}", source)
        for source in group.files
    ]


def static_resource_entries() -> list[ResourceEntry]:
    return sorted(entry for group in RESOURCE_GROUPS for entry in entries_of(group))
