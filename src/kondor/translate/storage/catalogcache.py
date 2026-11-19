import json
import time
from pathlib import Path
from typing import NamedTuple

from kondor.translate.download.catalogloader import Catalog, RawCatalog, build_catalog

CACHE_SECONDS = 24 * 60 * 60
SAVED_KEY = "saved"
ENGINE_KEY = "engine"
MODELS_KEY = "models"
BASE_URL_KEY = "base_url"


class CachedCatalog(NamedTuple):
    catalog: Catalog | None
    is_fresh: bool


def is_fresh(saved: object, now: float) -> bool:
    return isinstance(saved, (int, float)) and 0 <= now - saved < CACHE_SECONDS


def read_cache(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def raw_from_cache(cache: dict[str, object]) -> RawCatalog | None:
    engine, models, base_url = cache.get(ENGINE_KEY), cache.get(MODELS_KEY), cache.get(BASE_URL_KEY)
    if isinstance(engine, list) and isinstance(models, list) and isinstance(base_url, str):
        return RawCatalog(engine, models, base_url)
    return None


def load_cached(path: Path) -> CachedCatalog:
    cache = read_cache(path)
    raw = raw_from_cache(cache) if cache is not None else None
    if cache is None or raw is None:
        return CachedCatalog(None, False)
    return CachedCatalog(build_catalog(raw), is_fresh(cache.get(SAVED_KEY), time.time()))


def write_cache(path: Path, raw: RawCatalog) -> None:
    payload = {
        SAVED_KEY: time.time(),
        ENGINE_KEY: raw.engine,
        MODELS_KEY: raw.models,
        BASE_URL_KEY: raw.base_url,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
