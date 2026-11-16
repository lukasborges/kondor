from PySide6.QtCore import QCoreApplication, QSettings

from kondor.profiles.userprofile import DEFAULT_ID, UserProfile

ORGANIZATION = "KDE"
APPLICATION = "KondorProfiles"
ORDER_KEY = "Profiles/Order"
STARTUP_KEY = "Startup/Profile"
LAST_USED_KEY = "Startup/LastUsed"
DEFAULT_ICON = "im-user"


def open_registry() -> QSettings:
    return QSettings(ORGANIZATION, APPLICATION)


def as_text_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    return [str(item) for item in value] if isinstance(value, list) else []


def read_order(settings: QSettings) -> list[str]:
    order = as_text_list(settings.value(ORDER_KEY, []))
    return [DEFAULT_ID, *(item for item in order if item != DEFAULT_ID)]


def default_name() -> str:
    return str(QCoreApplication.translate("ProfileRegistry", "Default"))


def read_name(settings: QSettings, profile_id: str) -> str:
    fallback = default_name() if profile_id == DEFAULT_ID else profile_id
    return str(settings.value(f"Profiles/{profile_id}/Name", fallback))


def read_icon(settings: QSettings, profile_id: str) -> str:
    return str(settings.value(f"Profiles/{profile_id}/Icon", DEFAULT_ICON))


def read_profile(settings: QSettings, profile_id: str) -> UserProfile:
    return UserProfile(profile_id, read_name(settings, profile_id), read_icon(settings, profile_id))


def read_profiles(settings: QSettings) -> list[UserProfile]:
    return [read_profile(settings, profile_id) for profile_id in read_order(settings)]


def write_profile(settings: QSettings, profile: UserProfile) -> None:
    settings.setValue(f"Profiles/{profile.id}/Name", profile.name)
    settings.setValue(f"Profiles/{profile.id}/Icon", profile.icon_name)


def write_order(settings: QSettings, order: list[str]) -> None:
    settings.setValue(ORDER_KEY, order)
