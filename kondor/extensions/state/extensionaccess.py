from dataclasses import dataclass, field


@dataclass
class ExtensionAccess:
    matches: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)


def is_subset(candidate: list[str], allowed: list[str]) -> bool:
    return set(candidate) <= set(allowed)


def is_silent_update(update: ExtensionAccess, installed: ExtensionAccess) -> bool:
    return (
        is_subset(update.matches, installed.matches)
        and is_subset(update.permissions, installed.permissions)
        and is_subset(update.includes, installed.includes)
    )
