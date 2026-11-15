from collections.abc import Iterator
from contextlib import contextmanager

from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.pagescripts import user_scripts
from kondor.core.settings.settings import Settings


@contextmanager
def restored_settings(*names: str) -> Iterator[Settings]:
    settings = Settings.instance()
    previous = {name: settings.property(name) for name in names}
    try:
        yield settings
    finally:
        for name, value in previous.items():
            settings.setProperty(name, value)


def scripts_named(profile: QQuickWebEngineProfile, name: str) -> list[QWebEngineScript]:
    collection = user_scripts(profile)
    assert collection is not None
    return [script for script in collection.property("collection") if script.name() == name]
