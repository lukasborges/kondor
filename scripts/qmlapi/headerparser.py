import re

from .cppscan import (
    argument_counts,
    balanced_arguments,
    class_bodies,
    collapse_bodies,
    strip_comments,
)
from .model import ClassApi, Property, add_counts, normalize_type

PROPERTY_KEYWORDS = (
    "READ|WRITE|MEMBER|NOTIFY|CONSTANT|FINAL|RESET|REVISION|BINDABLE|DESIGNABLE|SCRIPTABLE|STORED"
    "|USER|REQUIRED"
)
PROPERTY_HEAD = re.compile(rf"^(.*?)\s*\b(?:{PROPERTY_KEYWORDS})\b", re.S)
SECTION = re.compile(
    r"\b(?P<label>(?:public|private|protected)(?:\s+(?:slots|Q_SLOTS))?|signals|Q_SIGNALS)\s*:(?!:)"
)
FUNCTION_NAME = re.compile(r"(\w+)\s*\(")
SLOT_LABELS = ("slots", "Q_SLOTS")
SIGNAL_LABELS = ("signals", "Q_SIGNALS")


def find_properties(body: str) -> dict[str, Property]:
    properties = {}
    for match in re.finditer(r"Q_PROPERTY\s*\(", body):
        text = balanced_arguments(body, match.end() - 1)
        head = PROPERTY_HEAD.match(text)
        words = head.group(1).split() if head else text.split()
        name = words[-1].lstrip("*&")
        type_part = " ".join(words[:-1]) + words[-1][: len(words[-1]) - len(name)]
        properties[name] = Property(normalize_type(type_part), is_writable(text))
    return properties


def is_writable(declaration: str) -> bool:
    has_member = re.search(r"\bMEMBER\b", declaration) is not None
    has_constant = re.search(r"\bCONSTANT\b", declaration) is not None
    return re.search(r"\bWRITE\b", declaration) is not None or (has_member and not has_constant)


def sections_of(body: str) -> list[tuple[str, str]]:
    matches = list(SECTION.finditer(body))
    starts = [(match.group("label"), match.end()) for match in matches]
    ends = [match.start() for match in matches[1:]] + [len(body)]
    first = [("private", body[: matches[0].start()])] if matches else [("private", body)]
    pairs = zip(starts, ends, strict=True)
    return first + [(label, body[start:end]) for (label, start), end in pairs]


IGNORED_STATEMENT = re.compile(r"Q_PROPERTY|Q_ENUM|^\s*using\s")


def is_macro_only(name: str, statement: str) -> bool:
    return name.startswith(("Q_", "QML_")) and "Q_INVOKABLE" not in statement


def declared_function(statement: str) -> tuple[str, set[int]] | None:
    if IGNORED_STATEMENT.search(statement):
        return None
    match = FUNCTION_NAME.search(statement)
    if match is None or is_macro_only(match.group(1), statement):
        return None
    return match.group(1), argument_counts(balanced_arguments(statement, match.end() - 1))


def add_functions(api: ClassApi, label: str, text: str) -> None:
    is_signal = label in SIGNAL_LABELS
    is_slot = label.rsplit(maxsplit=1)[-1] in SLOT_LABELS
    for statement in text.split(";"):
        function = declared_function(statement)
        invokable = "Q_INVOKABLE" in statement
        if function is None or not (is_signal or is_slot or invokable):
            continue
        add_counts(api.signals if is_signal else api.callables, *function)


def parse_class(name: str, body: str) -> ClassApi:
    flat = collapse_bodies(body)
    api = ClassApi(name, find_properties(flat))
    for label, text in sections_of(flat):
        add_functions(api, label, text)
    return api


def parse_header(text: str) -> dict[str, ClassApi]:
    bodies = class_bodies(strip_comments(text))
    return {name: parse_class(name, body) for name, body in bodies.items()}
