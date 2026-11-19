from kondor.core.settings.settings import Settings

ALWAYS = "translateAlways"
NEVER = "translateNever"
NEVER_HOSTS = "translateNeverHosts"
TARGET = "translateTo"


def stored(name: str) -> list[str]:
    return [str(item) for item in Settings.instance().property(name) or []]


def store(name: str, values: list[str]) -> None:
    Settings.instance().setProperty(name, values)


def with_member(values: list[str], item: str, is_member: bool) -> list[str]:
    remaining = [value for value in values if value != item]
    return [*remaining, item] if is_member else remaining


def is_listed(name: str, item: str) -> bool:
    return item in stored(name)


def set_listed(name: str, item: str, is_member: bool) -> None:
    store(name, with_member(stored(name), item, is_member))


def set_always(language: str, is_member: bool) -> None:
    set_listed(ALWAYS, language, is_member)
    if is_member:
        set_listed(NEVER, language, False)


def set_never(language: str, is_member: bool) -> None:
    set_listed(NEVER, language, is_member)
    if is_member:
        set_listed(ALWAYS, language, False)


def target_language() -> str:
    return str(Settings.instance().property(TARGET) or "en")
