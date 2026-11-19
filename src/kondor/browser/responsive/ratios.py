RATIOS = (1.0, 1.5, 2.0, 2.25, 2.5, 2.625, 3.0, 3.5, 4.0)
DEFAULT_RATIO = 1.0
MAX_TEXTURE = 8192


def max_ratio(width: int, height: int) -> float:
    return MAX_TEXTURE / max(width, height)


def fitted(ratio: float, width: int, height: int) -> float:
    allowed = [candidate for candidate in RATIOS if candidate <= max_ratio(width, height)]
    return min(ratio, allowed[-1]) if allowed else ratio
