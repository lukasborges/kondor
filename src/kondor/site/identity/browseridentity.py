from PySide6.QtCore import QObject, Slot

from kondor.site.identity import useragents


class BrowserIdentity(QObject):
    _instance: "BrowserIdentity | None" = None

    @classmethod
    def instance(cls) -> "BrowserIdentity":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(str, result=str)
    def choiceOf(self, agent: str) -> str:
        return useragents.choice_of(agent)
