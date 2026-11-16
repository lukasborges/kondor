from pathlib import Path

from PySide6.QtCore import QStandardPaths

from kondor.profiles import profilepaths
from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.userprofile import DEFAULT_ID

OTHER = "ab12cd34"


def app_data() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))


def test_default_keeps_the_legacy_locations() -> None:
    assert profilepaths.data_directory(DEFAULT_ID) == app_data()
    assert profilepaths.settings_application(DEFAULT_ID) == "Kondor"
    assert profilepaths.storage_name(DEFAULT_ID) == "kondor"
    assert profilepaths.wallet_folder(DEFAULT_ID) == "Kondor"


def test_other_profile_lives_under_its_own_folder() -> None:
    assert profilepaths.data_directory(OTHER) == app_data() / "profiles" / OTHER


def test_other_profile_has_its_own_settings_storage_and_wallet_folder() -> None:
    assert profilepaths.settings_application(OTHER) == f"Kondor-{OTHER}"
    assert profilepaths.storage_name(OTHER) == f"kondor-{OTHER}"
    assert profilepaths.wallet_folder(OTHER) == f"Kondor-{OTHER}"


def test_web_data_covers_the_data_and_cache_storage() -> None:
    directories = profilepaths.web_data_directories(OTHER)

    assert [path.name for path in directories] == [f"kondor-{OTHER}"] * 2
    assert all(path.parent.name == "QtWebEngine" for path in directories)


def test_active_profile_answers_for_default_before_selection() -> None:
    assert ActiveProfile.id() == DEFAULT_ID
    assert ActiveProfile.data_directory() == app_data()


def test_active_profile_answers_for_the_selected_profile() -> None:
    ActiveProfile.select(OTHER)

    assert ActiveProfile.data_directory() == app_data() / "profiles" / OTHER
    assert ActiveProfile.data_directory().is_dir()
    assert ActiveProfile.settings().fileName().endswith(f"Kondor-{OTHER}.conf")
    assert ActiveProfile.storage_name() == f"kondor-{OTHER}"
