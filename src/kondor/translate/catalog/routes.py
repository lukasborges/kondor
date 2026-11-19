PIVOT_LANGUAGE = "en"
Pair = tuple[str, str]


def plan_route(available: set[Pair], source: str, target: str) -> list[Pair] | None:
    if source == target:
        return None
    if (source, target) in available:
        return [(source, target)]
    through_pivot = [(source, PIVOT_LANGUAGE), (PIVOT_LANGUAGE, target)]
    return through_pivot if all(pair in available for pair in through_pivot) else None


def source_languages(available: set[Pair]) -> list[str]:
    return sorted({source for source, _ in available} | {PIVOT_LANGUAGE})


def target_languages(available: set[Pair]) -> list[str]:
    return sorted({target for _, target in available} | {PIVOT_LANGUAGE})


def can_translate(available: set[Pair], source: str, target: str) -> bool:
    return plan_route(available, source, target) is not None
