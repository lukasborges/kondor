from pathlib import Path

from kondor.browser.profile.pagescripts import WEB_CHANNEL_RESOURCE, read_resource

PAGE_FILES = (
    (":/translate/engine.html", "engine.html"),
    (":/translate/engine.js", "engine.js"),
    (":/translate/bergamot-translator.js", "bergamot-translator.js"),
    (":/translate/translations-engine.worker.js", "translations-engine.worker.js"),
    (WEB_CHANNEL_RESOURCE, "qwebchannel.js"),
)
ENTRY_FILE = "engine.html"


def write_page(directory: Path) -> Path | None:
    directory.mkdir(parents=True, exist_ok=True)
    for resource, name in PAGE_FILES:
        source = read_resource(resource)
        if source is None:
            return None
        (directory / name).write_text(source, encoding="utf-8")
    return directory / ENTRY_FILE
