from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from tests.browser.profile.profilesupport import restored_settings
from tests.history.historyrows import add_visit, now_ms, reset_history, titles

pytestmark = pytest.mark.no_qt_log

Policy = QQuickWebEngineProfile.PersistentPermissionsPolicy
Cookies = QQuickWebEngineProfile.PersistentCookiesPolicy


@pytest.fixture
def manager(qapp: object, staged_resources: None) -> ProfileManager:
    return ProfileManager.instance()


def test_profiles_store_normal_decisions_and_keep_private_ones_in_memory(
    manager: ProfileManager,
) -> None:
    assert manager.defaultProfile().persistentPermissionsPolicy() == Policy.StoreOnDisk
    private = manager.createPrivateProfile()
    assert private.isOffTheRecord()
    assert private.persistentPermissionsPolicy() == Policy.StoreInMemory


def test_default_profile_is_the_persistent_kondor_profile(
    manager: ProfileManager, isolated_profile: Path
) -> None:
    profile = manager.defaultProfile()
    assert profile.storageName() == "kondor"
    assert not profile.isOffTheRecord()
    assert profile.persistentCookiesPolicy() == Cookies.AllowPersistentCookies
    storage = Path(profile.persistentStoragePath())
    assert storage.parts[-2:] == ("QtWebEngine", "kondor")
    assert storage.is_relative_to(isolated_profile)
    assert manager.defaultProfile() is profile
    assert profile.parent() is manager


def test_private_profile_is_listed_until_destroyed(manager: ProfileManager, qtbot: QtBot) -> None:
    default, private = manager.defaultProfile(), manager.createPrivateProfile()
    assert manager.profiles()[0] is default
    assert private in manager.profiles()
    private.deleteLater()
    qtbot.waitUntil(lambda: private not in manager.profiles())


def test_profile_created_is_emitted_for_every_profile(
    manager: ProfileManager, qtbot: QtBot
) -> None:
    with qtbot.waitSignal(manager.profileCreated) as blocker:
        private = manager.createPrivateProfile()
    assert blocker.args == [private]


def test_home_page_and_addresses_follow_settings(manager: ProfileManager, qtbot: QtBot) -> None:
    with restored_settings("homePage", "searchEngine") as settings:
        with qtbot.waitSignal(manager.homePageChanged):
            settings.setProperty("homePage", "https://home.example/")
        settings.setProperty("searchEngine", "duckduckgo")
        assert manager.property("homePage") == "https://home.example/"
        assert manager.resolveAddress("") == QUrl("https://home.example/")
        assert manager.resolveAddress("kde") == QUrl("https://duckduckgo.com/?q=kde")
        assert manager.addressUrl("kde.org") == QUrl("https://kde.org")
        assert manager.searchUrl("a b") == QUrl("https://duckduckgo.com/?q=a%20b")


def test_certificate_overrides_are_per_profile_and_case_insensitive(
    manager: ProfileManager,
) -> None:
    default, private = manager.defaultProfile(), manager.createPrivateProfile()
    manager.mark_certificate_overridden(default, "KDE.org")
    assert manager.is_certificate_overridden(default, "kde.org")
    assert not manager.is_certificate_overridden(private, "kde.org")


def test_download_directory_change_reaches_every_profile(
    manager: ProfileManager, tmp_path: Path
) -> None:
    default, private = manager.defaultProfile(), manager.createPrivateProfile()
    with restored_settings("downloadDirectory") as settings:
        settings.setProperty("downloadDirectory", str(tmp_path))
        assert default.downloadPath() == str(tmp_path)
        assert private.downloadPath() == str(tmp_path)


def test_clear_data_on_exit_clears_history_only_when_enabled(manager: ProfileManager) -> None:
    reset_history()
    add_visit("https://kde.org/", "KDE", now_ms())
    with restored_settings("clearDataOnExit") as settings:
        settings.setProperty("clearDataOnExit", False)
        QCoreApplication.instance().aboutToQuit.emit()
        assert titles() == ["KDE"]
        settings.setProperty("clearDataOnExit", True)
        QCoreApplication.instance().aboutToQuit.emit()
        assert titles() == []
