from pathlib import Path

from PySide6.QtCore import QStandardPaths

from kondor.profiles.userprofile import DEFAULT_ID

APPLICATION = "Kondor"
PROFILES_FOLDER = "profiles"
WEB_ENGINE_FOLDER = "QtWebEngine"


def is_default(profile_id: str) -> bool:
    return profile_id == DEFAULT_ID


def suffixed(base: str, profile_id: str) -> str:
    return base if is_default(profile_id) else f"{base}-{profile_id}"


def app_data_directory() -> Path:
    location = QStandardPaths.StandardLocation.AppDataLocation
    return Path(QStandardPaths.writableLocation(location))


def cache_directory() -> Path:
    location = QStandardPaths.StandardLocation.CacheLocation
    return Path(QStandardPaths.writableLocation(location))


def data_directory(profile_id: str) -> Path:
    if is_default(profile_id):
        return app_data_directory()
    return app_data_directory() / PROFILES_FOLDER / profile_id


def settings_application(profile_id: str) -> str:
    return suffixed(APPLICATION, profile_id)


def storage_name(profile_id: str) -> str:
    return suffixed(APPLICATION.lower(), profile_id)


def wallet_folder(profile_id: str) -> str:
    return suffixed(APPLICATION, profile_id)


def web_data_directories(profile_id: str) -> list[Path]:
    name = storage_name(profile_id)
    base_directories = (app_data_directory(), cache_directory())
    return [base / WEB_ENGINE_FOLDER / name for base in base_directories]
