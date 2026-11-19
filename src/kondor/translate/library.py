from typing import ClassVar, Self

from PySide6.QtCore import Property, QObject, Signal, Slot

from kondor.translate.languagenames import language_name
from kondor.translate.service import TranslationService
from kondor.translate.storage.translationstore import InstalledPair
from kondor.translate.translationflow import megabytes, pair_label


def describe(pair: InstalledPair) -> dict[str, object]:
    return {
        "source": pair.source,
        "target": pair.target,
        "label": pair_label(pair.source, pair.target),
        "megabytes": megabytes(pair.size_bytes),
    }


class TranslationLibrary(QObject):
    _instance: ClassVar["TranslationLibrary | None"] = None
    installedChanged = Signal()

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Property("QVariantList", notify=installedChanged)
    def installed(self) -> list[dict[str, object]]:
        return [describe(pair) for pair in TranslationService.instance().installed_pairs()]

    @Slot(str, result=str)
    def languageName(self, code: str) -> str:
        return language_name(code)

    @Slot()
    def refresh(self) -> None:
        self.installedChanged.emit()

    @Slot(str, str)
    def remove(self, source: str, target: str) -> None:
        TranslationService.instance().remove_pair(source, target)
        self.installedChanged.emit()
