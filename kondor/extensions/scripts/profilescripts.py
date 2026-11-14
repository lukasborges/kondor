from typing import Any

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QTimer
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.pagescripts import user_scripts


def call_on_collection(collection: QObject, method: str, script: QWebEngineScript) -> None:
    QMetaObject.invokeMethod(collection, method, Q_ARG(QWebEngineScript, script))


class ProfileScripts(QObject):
    def __init__(self, manager: Any) -> None:
        super().__init__(manager)
        self.manager = manager
        self.profiles: dict[int, QQuickWebEngineProfile] = {}
        self.inserted: dict[int, list[QWebEngineScript]] = {}
        self.is_rebuild_queued = False

    def register_profile(self, profile: QQuickWebEngineProfile | None) -> None:
        if profile is None:
            return
        key = id(profile)
        self.profiles[key] = profile
        profile.destroyed.connect(lambda: self.forget_profile(key))
        self.apply_scripts(profile)

    def forget_profile(self, key: int) -> None:
        self.profiles.pop(key, None)
        self.inserted.pop(key, None)

    def remove_inserted(self, profile: QQuickWebEngineProfile, collection: QObject) -> None:
        for script in self.inserted.pop(id(profile), []):
            call_on_collection(collection, "remove", script)

    def apply_scripts(self, profile: QQuickWebEngineProfile) -> None:
        collection = user_scripts(profile)
        if collection is None:
            return
        self.remove_inserted(profile, collection)
        scripts = self.manager.scripts_for(profile.isOffTheRecord())
        for script in scripts:
            call_on_collection(collection, "insert", script)
        self.inserted[id(profile)] = scripts

    def rebuild_all(self) -> None:
        self.is_rebuild_queued = False
        for profile in list(self.profiles.values()):
            self.apply_scripts(profile)

    def rebuild_once_after_several_changes(self) -> None:
        if self.is_rebuild_queued:
            return
        self.is_rebuild_queued = True
        QTimer.singleShot(0, self.rebuild_all)
