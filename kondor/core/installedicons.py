from PySide6.QtCore import QObject, QStandardPaths, Slot

ICON_FOLDER = "icons/hicolor/scalable/actions/"


class InstalledIcons(QObject):
    _instance: "InstalledIcons | None" = None

    @classmethod
    def instance(cls) -> "InstalledIcons":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(str, result=bool)
    def isInstalled(self, iconName: str) -> bool:  # noqa: N803
        relative_path = f"{ICON_FOLDER}{iconName}.svg"
        location = QStandardPaths.GenericDataLocation
        return bool(QStandardPaths.locate(location, relative_path))
