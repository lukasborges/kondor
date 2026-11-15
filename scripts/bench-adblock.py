#!/usr/bin/env python3
import statistics
import sys
import time
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QUrl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kondor.adblock.filters.filterengine import FilterEngine, ResourceKind  # noqa: E402
from kondor.adblock.lists.filterlists import parse_filter_lists  # noqa: E402

DATA = ROOT / "tests" / "data" / "adblock"
LISTS = ("easylist.txt", "easyprivacy.txt")
ROUNDS = 5
MEDIAN_BUDGET_US = 50.0
P99_BUDGET_US = 500.0
NANOSECONDS_PER_MICROSECOND = 1000.0
PERCENTILES = 100
P99_INDEX = 98


class Request(NamedTuple):
    url: QUrl
    first_party_host: str
    kind: ResourceKind


def read_requests() -> list[Request]:
    lines = (DATA / "requests.txt").read_text(encoding="utf-8").splitlines()
    parts = [line.split(" ", 2) for line in lines if line]
    return [Request(QUrl(url), host, ResourceKind[kind]) for kind, host, url in parts]


def build_engine() -> tuple[FilterEngine, float]:
    start = time.perf_counter()
    engine = parse_filter_lists([str(DATA / name) for name in LISTS])
    return engine, time.perf_counter() - start


def timed_round(engine: FilterEngine, requests: list[Request]) -> tuple[list[float], int]:
    timings: list[float] = []
    blocked = 0
    for request in requests:
        start = time.perf_counter_ns()
        blocked += engine.should_block(*request)
        timings.append((time.perf_counter_ns() - start) / NANOSECONDS_PER_MICROSECOND)
    return timings, blocked


def timed_rounds(engine: FilterEngine, requests: list[Request]) -> tuple[list[float], int]:
    timed_round(engine, requests)
    rounds = [timed_round(engine, requests) for _ in range(ROUNDS)]
    return [timing for timings, _ in rounds for timing in timings], rounds[0][1]


def main() -> int:
    engine, parse_seconds = build_engine()
    requests = read_requests()
    timings, blocked = timed_rounds(engine, requests)
    median = statistics.median(timings)
    p99 = statistics.quantiles(timings, n=PERCENTILES)[P99_INDEX]
    print(f"rules: {engine.rule_count()}\nparse: {parse_seconds:.2f} s")
    print(f"requests: {len(requests)}\nblocked: {blocked}")
    print(f"median: {median:.1f} µs\np99: {p99:.1f} µs")
    return 0 if median <= MEDIAN_BUDGET_US and p99 <= P99_BUDGET_US else 1


if __name__ == "__main__":
    sys.exit(main())
