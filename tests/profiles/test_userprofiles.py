from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from kondor.profiles import profilepaths
from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.registry.profileregistry import ProfileRegistry
from kondor.profiles.userprofile import DEFAULT_ID
from kondor.profiles.userprofiles import UserProfiles

ICON_COUNT = 8


@pytest.fixture
def profiles() -> UserProfiles:
    instance = UserProfiles.instance()
    instance.reload()
    return instance


@pytest.fixture(autouse=True)
def no_wallet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KONDOR_NO_KWALLET", "1")


def test_single_profile_is_the_default(profiles: UserProfiles) -> None:
    assert profiles.currentId == DEFAULT_ID
    assert profiles.currentName == "Default"
    assert not profiles.hasSeveralProfiles


def test_created_profile_is_listed(profiles: UserProfiles) -> None:
    profile_id = profiles.createProfile("Work", "flag")

    assert profiles.hasSeveralProfiles
    assert [item["id"] for item in profiles.profiles] == [DEFAULT_ID, profile_id]


def test_change_made_elsewhere_is_picked_up_by_reload(profiles: UserProfiles) -> None:
    changes: list[int] = []
    profiles.profilesChanged.connect(lambda: changes.append(1))

    ProfileRegistry().add("Work", "flag")
    profiles.reload()

    assert changes == [1]


def test_edit_renames_the_profile(profiles: UserProfiles) -> None:
    profile_id = profiles.createProfile("Work", "flag")

    profiles.editProfile(profile_id, "Office", "globe")

    assert profiles.profiles[1] == {"id": profile_id, "name": "Office", "iconName": "globe"}


def test_name_error_names_duplicates(profiles: UserProfiles) -> None:
    assert profiles.nameError("default", "") != ""
    assert profiles.nameError("Fresh", "") == ""


def test_default_cannot_be_deleted(profiles: UserProfiles) -> None:
    assert not profiles.deleteProfile(DEFAULT_ID)


def test_active_profile_cannot_be_deleted(profiles: UserProfiles) -> None:
    profile_id = profiles.createProfile("Work", "flag")
    ActiveProfile.select(profile_id)

    assert not profiles.deleteProfile(profile_id)


def test_deleting_a_stopped_profile_removes_its_data(profiles: UserProfiles) -> None:
    profile_id = profiles.createProfile("Work", "flag")
    directory = profilepaths.data_directory(profile_id)
    directory.mkdir(parents=True)

    assert profiles.deleteProfile(profile_id)
    QCoreApplication.processEvents()

    assert not directory.exists()
    assert not profiles.hasSeveralProfiles


def test_startup_choice_round_trips_through_ask(profiles: UserProfiles) -> None:
    profiles.startupProfileId = ""

    assert profiles.startupProfileId == ""
    assert ProfileRegistry().startup_profile_id() == "ask"


def test_icon_names_are_the_eight_profile_icons(profiles: UserProfiles) -> None:
    assert len(profiles.iconNames()) == ICON_COUNT


def test_removed_profile_leaves_no_folder_under_profiles(profiles: UserProfiles) -> None:
    profile_id = profiles.createProfile("Work", "flag")
    profilepaths.data_directory(profile_id).mkdir(parents=True)
    profiles.deleteProfile(profile_id)

    assert not Path(profilepaths.data_directory(profile_id)).exists()
