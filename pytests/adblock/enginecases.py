from typing import NamedTuple

from PySide6.QtCore import QUrl

from kondor.adblock.filters.filterengine import FilterEngine, ResourceKind


class Request(NamedTuple):
    url: str
    page: str
    kind: ResourceKind = ResourceKind.SCRIPT


def engine_with(*rules: str) -> FilterEngine:
    engine = FilterEngine()
    for rule in rules:
        engine.add_rule(rule)
    return engine


def blocked(engine: FilterEngine, request: Request) -> bool:
    return engine.should_block(QUrl(request.url), request.page, request.kind)
