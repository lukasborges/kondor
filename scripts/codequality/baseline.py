import json
import os
from typing import Dict, List, Optional, Set

from .rules import Violation

Baseline = Dict[str, Dict[str, int]]


def load_baseline(path: str) -> Baseline:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_baseline(path: str, baseline: Baseline) -> None:
    ordered = {rule: dict(sorted(entries.items())) for rule, entries in sorted(baseline.items())}
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(ordered, indent=2) + "\n")


def build_baseline(violations: List[Violation]) -> Baseline:
    baseline: Baseline = {}
    for violation in violations:
        baseline.setdefault(violation.rule, {})[violation.key] = violation.value
    return baseline


def path_of(key: str) -> str:
    return key.split("::")[0]


def describe(violation: Violation, suffix: str = "") -> str:
    path = path_of(violation.key)
    return "%s:%d: %s: %d > %d (%s)%s" % (
        path, violation.line, violation.rule, violation.value, violation.limit, violation.key, suffix)


def violation_problem(violation: Violation, baseline: Baseline) -> Optional[str]:
    allowed = baseline.get(violation.rule, {}).get(violation.key)
    if allowed is None:
        return describe(violation)
    if violation.value > allowed:
        return describe(violation, " grew from baseline %d" % allowed)
    return None


def fixed_problems(violations: List[Violation], baseline: Baseline, paths: Optional[Set[str]]) -> List[str]:
    current = {(violation.rule, violation.key) for violation in violations}
    return ["%s:1: fixed: remove it from the baseline (%s %s)" % (path_of(key), rule, key)
            for rule, entries in sorted(baseline.items()) for key in sorted(entries)
            if (rule, key) not in current and (paths is None or path_of(key) in paths)]


def find_problems(violations: List[Violation], baseline: Baseline, paths: Optional[Set[str]]) -> List[str]:
    problems = [violation_problem(violation, baseline) for violation in violations]
    return [problem for problem in problems if problem] + fixed_problems(violations, baseline, paths)


def lowered_baseline(violations: List[Violation], baseline: Baseline) -> Baseline:
    return build_baseline([violation for violation in violations
                           if violation.key in baseline.get(violation.rule, {})])


def can_initialize(path: str) -> bool:
    return not os.path.exists(path)
