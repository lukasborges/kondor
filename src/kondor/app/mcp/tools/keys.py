from kondor.app.mcp.cdp.pagesession import PageSession
from kondor.app.mcp.protocol.toolresult import ToolFailureError

MODIFIER_BITS = {"alt": 1, "ctrl": 2, "control": 2, "meta": 4, "cmd": 4, "shift": 8}
NAMED_KEYS = {
    "enter": ("Enter", "Enter", 13),
    "escape": ("Escape", "Escape", 27),
    "tab": ("Tab", "Tab", 9),
    "backspace": ("Backspace", "Backspace", 8),
    "delete": ("Delete", "Delete", 46),
    "space": (" ", "Space", 32),
    "arrowleft": ("ArrowLeft", "ArrowLeft", 37),
    "arrowup": ("ArrowUp", "ArrowUp", 38),
    "arrowright": ("ArrowRight", "ArrowRight", 39),
    "arrowdown": ("ArrowDown", "ArrowDown", 40),
    "home": ("Home", "Home", 36),
    "end": ("End", "End", 35),
    "pageup": ("PageUp", "PageUp", 33),
    "pagedown": ("PageDown", "PageDown", 34),
}
TEXT_KEYS = ("Enter",)


def split_combo(combo: str) -> tuple[int, str]:
    *modifier_names, key_name = combo.split("+") if combo != "+" else [combo]
    modifiers = 0
    for name in modifier_names:
        modifiers |= MODIFIER_BITS.get(name.lower(), 0)
    return modifiers, key_name


def describe_key(key_name: str) -> tuple[str, str, int]:
    named = NAMED_KEYS.get(key_name.lower())
    if named is not None:
        return named
    if len(key_name) != 1:
        raise ToolFailureError(f"Unknown key: {key_name}")
    return (
        key_name,
        f"Key{key_name.upper()}" if key_name.isalpha() else key_name,
        ord(key_name.upper()),
    )


def key_event(kind: str, key: tuple[str, str, int], modifiers: int) -> dict[str, object]:
    event: dict[str, object] = {
        "type": kind,
        "key": key[0],
        "code": key[1],
        "windowsVirtualKeyCode": key[2],
        "modifiers": modifiers,
    }
    if kind == "keyDown" and should_insert_text(key, modifiers):
        event.update({"type": "keyDown", "text": "\r" if key[0] == "Enter" else key[0]})
    return event


def should_insert_text(key: tuple[str, str, int], modifiers: int) -> bool:
    is_plain_modifier = modifiers & ~MODIFIER_BITS["shift"]
    return not is_plain_modifier and (len(key[0]) == 1 or key[0] in TEXT_KEYS)


def press(session: PageSession, combo: str) -> None:
    modifiers, key_name = split_combo(combo)
    key = describe_key(key_name)
    session.call("Input.dispatchKeyEvent", key_event("keyDown", key, modifiers))
    session.call("Input.dispatchKeyEvent", key_event("keyUp", key, modifiers))
