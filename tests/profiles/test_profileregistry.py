from pathlib import Path

from kondor.profiles.registry.profileregistry import ProfileRegistry
from kondor.profiles.registry.registrystore import open_registry
from kondor.profiles.userprofile import ASK_EVERY_TIME, DEFAULT_ID

ID_LENGTH = 8


def test_holds_only_default_without_a_registry_file() -> None:
    profiles = ProfileRegistry().profiles()

    assert [(profile.id, profile.name, profile.icon_name) for profile in profiles] == [
        (DEFAULT_ID, "Default", "im-user")
    ]


def test_writes_nothing_until_the_user_changes_something() -> None:
    ProfileRegistry().profiles()
    ProfileRegistry().startup_profile_id()

    assert not Path(open_registry().fileName()).exists()


def test_added_profile_follows_default_in_creation_order() -> None:
    registry = ProfileRegistry()
    work = registry.add("  Work ", "view-pim-tasks")
    shopping = registry.add("Shopping", "globe")

    assert [profile.id for profile in registry.profiles()] == [DEFAULT_ID, work.id, shopping.id]
    assert registry.profiles()[1].name == "Work"


def test_added_profile_gets_an_eight_character_id() -> None:
    assert len(ProfileRegistry().add("Work", "flag").id) == ID_LENGTH


def test_unknown_icon_falls_back_to_the_first_icon() -> None:
    assert ProfileRegistry().add("Work", "not-an-icon").icon_name == "im-user"


def test_update_renames_without_changing_the_id() -> None:
    registry = ProfileRegistry()
    work = registry.add("Work", "flag")
    registry.update(type(work)(work.id, "Office", "globe"))

    assert registry.find(work.id) == type(work)(work.id, "Office", "globe")


def test_default_can_be_renamed() -> None:
    registry = ProfileRegistry()
    default = registry.profiles()[0]
    registry.update(type(default)(DEFAULT_ID, "Personal", "go-home"))

    assert registry.profiles()[0].name == "Personal"


def test_find_matches_names_without_regard_to_case() -> None:
    registry = ProfileRegistry()
    work = registry.add("Work", "flag")

    assert registry.find("wORK") == work


def test_find_prefers_an_id_over_a_name() -> None:
    registry = ProfileRegistry()
    work = registry.add("Work", "flag")
    registry.add(work.id, "globe")

    assert registry.find(work.id) == work


def test_find_returns_nothing_for_an_unknown_name() -> None:
    assert ProfileRegistry().find("nobody") is None


def test_empty_name_is_rejected() -> None:
    assert ProfileRegistry().name_error("   ") != ""


def test_name_longer_than_sixty_four_characters_is_rejected() -> None:
    assert ProfileRegistry().name_error("x" * 65) != ""


def test_duplicate_name_is_rejected_without_regard_to_case() -> None:
    registry = ProfileRegistry()
    registry.add("Work", "flag")

    assert registry.name_error("WORK") == "A profile with this name already exists."


def test_own_name_is_accepted_when_editing() -> None:
    registry = ProfileRegistry()
    work = registry.add("Work", "flag")

    assert registry.name_error("work", work.id) == ""


def test_remove_forgets_the_profile() -> None:
    registry = ProfileRegistry()
    work = registry.add("Work", "flag")
    registry.remove(work.id)

    assert registry.find(work.id) is None


def test_default_cannot_be_removed() -> None:
    registry = ProfileRegistry()
    registry.remove(DEFAULT_ID)

    assert [profile.id for profile in registry.profiles()] == [DEFAULT_ID]


def test_startup_profile_is_default_at_first() -> None:
    assert ProfileRegistry().startup_profile_id() == DEFAULT_ID


def test_startup_profile_can_ask_every_time() -> None:
    registry = ProfileRegistry()
    registry.set_startup_profile_id(ASK_EVERY_TIME)

    assert registry.startup_profile_id() == ASK_EVERY_TIME


def test_startup_profile_falls_back_to_default_after_its_removal() -> None:
    registry = ProfileRegistry()
    work = registry.add("Work", "flag")
    registry.set_startup_profile_id(work.id)
    registry.remove(work.id)

    assert registry.startup_profile_id() == DEFAULT_ID


def test_last_used_profile_is_remembered_and_falls_back_after_removal() -> None:
    registry = ProfileRegistry()
    work = registry.add("Work", "flag")
    registry.set_last_used_id(work.id)
    assert registry.last_used_id() == work.id

    registry.remove(work.id)
    assert registry.last_used_id() == DEFAULT_ID
