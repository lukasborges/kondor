from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QSettings

from kondor.profiles import profilepaths
from kondor.profiles.userprofile import DEFAULT_ID

ORGANIZATION = "KDE"


class ActiveProfile:
    _id: ClassVar[str] = DEFAULT_ID

    @classmethod
    def select(cls, profile_id: str) -> None:
        cls._id = profile_id

    @classmethod
    def id(cls) -> str:
        return cls._id

    @classmethod
    def is_default(cls) -> bool:
        return profilepaths.is_default(cls._id)

    @classmethod
    def data_directory(cls) -> Path:
        directory = profilepaths.data_directory(cls._id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @classmethod
    def settings(cls) -> QSettings:
        return QSettings(ORGANIZATION, profilepaths.settings_application(cls._id))

    @classmethod
    def storage_name(cls) -> str:
        return profilepaths.storage_name(cls._id)

    @classmethod
    def wallet_folder(cls) -> str:
        return profilepaths.wallet_folder(cls._id)
