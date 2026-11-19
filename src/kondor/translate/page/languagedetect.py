import importlib
from types import ModuleType

MIN_SAMPLE_CHARACTERS = 20


def load_detector() -> ModuleType | None:
    try:
        return importlib.import_module("langdetect")
    except ImportError:
        return None


def primary_subtag(tag: str) -> str:
    return tag.replace("_", "-").split("-")[0].strip().lower()


def declared_language(tag: str) -> str | None:
    primary = primary_subtag(tag)
    return primary if primary and primary != "und" else None


def detect_language(sample: str) -> str | None:
    if len(sample.strip()) < MIN_SAMPLE_CHARACTERS:
        return None
    module = load_detector()
    if module is None:
        return None
    module.DetectorFactory.seed = 0
    try:
        return primary_subtag(str(module.detect(sample[:2000])))
    except Exception:  # noqa: BLE001
        return None


def page_language(declared: str, sample: str) -> str | None:
    return declared_language(declared) or detect_language(sample)
