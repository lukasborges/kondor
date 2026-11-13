import re
from dataclasses import dataclass, field


@dataclass
class Property:
    type_name: str
    is_writable: bool


@dataclass
class ClassApi:
    name: str
    properties: dict[str, Property] = field(default_factory=dict)
    callables: dict[str, set[int]] = field(default_factory=dict)
    signals: dict[str, set[int]] = field(default_factory=dict)


def normalize_type(type_name: str) -> str:
    without_const = re.sub(r"\bconst\b", "", type_name)
    return re.sub(r"[&*\s]", "", without_const)


def add_counts(target: dict[str, set[int]], name: str, counts: set[int]) -> None:
    target.setdefault(name, set()).update(counts)
