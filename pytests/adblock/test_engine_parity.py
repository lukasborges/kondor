import json
from pathlib import Path

from PySide6.QtCore import QUrl

from kondor.adblock.filters.filterengine import FilterEngine, ResourceKind
from kondor.adblock.lists.filterlists import parse_filter_lists

DATA = Path(__file__).resolve().parent.parent / "data" / "adblock"
LISTS = ("easylist.txt", "easyprivacy.txt")
SHOWN_DIFFERENCES = 10


def request_lines() -> list[str]:
    return (DATA / "requests.txt").read_text(encoding="utf-8").splitlines()


def is_blocked(engine: FilterEngine, line: str) -> bool:
    kind, first_party_host, url = line.split(" ", 2)
    return engine.should_block(QUrl(url), first_party_host, ResourceKind[kind])


def differences(lines: list[str], blocked: set[int], expected: set[int]) -> str:
    shown = sorted(blocked ^ expected)[:SHOWN_DIFFERENCES]
    return "\n".join(f"{index} blocked={index in blocked}: {lines[index]}" for index in shown)


def test_matches_the_cpp_engine_on_real_requests() -> None:
    expected = json.loads((DATA / "expected.json").read_text(encoding="utf-8"))
    engine = parse_filter_lists([str(DATA / name) for name in LISTS])
    lines = request_lines()
    blocked = {index for index, line in enumerate(lines) if is_blocked(engine, line)}
    assert engine.rule_count() == expected["ruleCount"]
    expected_blocked = set(expected["blocked"])
    assert blocked == expected_blocked, differences(lines, blocked, expected_blocked)
