from PySide6.QtCore import QCoreApplication, QUuid

from kondor.profiles.registry import registrystore
from kondor.profiles.registry.registrystore import open_registry
from kondor.profiles.userprofile import (
    ASK_EVERY_TIME,
    DEFAULT_ID,
    MAX_NAME_LENGTH,
    PROFILE_ICONS,
    UserProfile,
)

ID_LENGTH = 8


def new_profile_id() -> str:
    return str(QUuid.createUuid().toString(QUuid.StringFormat.Id128))[:ID_LENGTH]


def checked_icon(icon_name: str) -> str:
    return icon_name if icon_name in PROFILE_ICONS else PROFILE_ICONS[0]


def error_for_shape(name: str) -> str:
    if not name:
        return str(QCoreApplication.translate("ProfileRegistry", "Enter a name."))
    if len(name) > MAX_NAME_LENGTH:
        return str(QCoreApplication.translate("ProfileRegistry", "The name is too long."))
    return ""


class ProfileRegistry:
    def profiles(self) -> list[UserProfile]:
        return registrystore.read_profiles(open_registry())

    def find(self, name_or_id: str) -> UserProfile | None:
        profiles = self.profiles()
        by_id = next((profile for profile in profiles if profile.id == name_or_id), None)
        if by_id is not None:
            return by_id
        wanted = name_or_id.strip().casefold()
        return next((profile for profile in profiles if profile.name.casefold() == wanted), None)

    def add(self, name: str, icon_name: str) -> UserProfile:
        settings = open_registry()
        profile = UserProfile(new_profile_id(), name.strip(), checked_icon(icon_name))
        order = registrystore.read_order(settings)
        registrystore.write_order(settings, [*order, profile.id])
        registrystore.write_profile(settings, profile)
        return profile

    def update(self, profile: UserProfile) -> None:
        settings = open_registry()
        trimmed = UserProfile(profile.id, profile.name.strip(), checked_icon(profile.icon_name))
        registrystore.write_profile(settings, trimmed)

    def remove(self, profile_id: str) -> None:
        if profile_id == DEFAULT_ID:
            return
        settings = open_registry()
        order = [item for item in registrystore.read_order(settings) if item != profile_id]
        registrystore.write_order(settings, order)
        settings.remove(f"Profiles/{profile_id}")

    def name_error(self, name: str, except_id: str = "") -> str:
        trimmed = name.strip()
        shape_error = error_for_shape(trimmed)
        if shape_error:
            return shape_error
        taken = any(
            profile.name.casefold() == trimmed.casefold() and profile.id != except_id
            for profile in self.profiles()
        )
        return self._duplicate_message() if taken else ""

    @staticmethod
    def _duplicate_message() -> str:
        return str(
            QCoreApplication.translate(
                "ProfileRegistry", "A profile with this name already exists."
            )
        )

    def startup_profile_id(self) -> str:
        value = str(open_registry().value(registrystore.STARTUP_KEY, DEFAULT_ID))
        return value if value == ASK_EVERY_TIME else self._existing_or_default(value)

    def set_startup_profile_id(self, value: str) -> None:
        open_registry().setValue(registrystore.STARTUP_KEY, value)

    def last_used_id(self) -> str:
        value = str(open_registry().value(registrystore.LAST_USED_KEY, DEFAULT_ID))
        return self._existing_or_default(value)

    def set_last_used_id(self, profile_id: str) -> None:
        open_registry().setValue(registrystore.LAST_USED_KEY, profile_id)

    def _existing_or_default(self, profile_id: str) -> str:
        exists = any(profile.id == profile_id for profile in self.profiles())
        return profile_id if exists else DEFAULT_ID
