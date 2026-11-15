from typing import NamedTuple


class Engine(NamedTuple):
    name: str
    url_template: str


CUSTOM_ENGINE = "custom"
QUERY_PLACEHOLDER = "%1"
FALLBACK_ENGINE = Engine("DuckDuckGo", "https://duckduckgo.com/?q=%1")
BUILT_IN_ENGINES = {
    "duckduckgo": FALLBACK_ENGINE,
    "google": Engine("Google", "https://www.google.com/search?q=%1"),
    "startpage": Engine("Startpage", "https://www.startpage.com/do/search?q=%1"),
    "brave": Engine("Brave Search", "https://search.brave.com/search?q=%1"),
}


def is_usable_custom_engine(engine_id: str, custom_url: str) -> bool:
    return engine_id == CUSTOM_ENGINE and QUERY_PLACEHOLDER in custom_url


def engine_for(engine_id: str) -> Engine:
    return BUILT_IN_ENGINES.get(engine_id, FALLBACK_ENGINE)


def url_template(engine_id: str, custom_url: str) -> str:
    if is_usable_custom_engine(engine_id, custom_url):
        return custom_url
    return engine_for(engine_id).url_template


def display_name(engine_id: str, custom_url: str) -> str:
    if is_usable_custom_engine(engine_id, custom_url):
        return ""
    return engine_for(engine_id).name
