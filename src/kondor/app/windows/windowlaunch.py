from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QUrl, qWarning

from kondor.app.commandline.extensionpackages import take_extension_packages
from kondor.app.commandline.startupargs import StartupArgs
from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.instance.windowactivation import raise_window
from kondor.app.remotecontrol.remotecontrolstartup import warn_private_refused
from kondor.app.windows.windowcontents import WindowContents
from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.session.sessionmanager import SessionManager
from kondor.browser.session.sessionwindow import SessionWindow
from kondor.core.settings.settings import Settings
from kondor.extensions.extensionmanager import ExtensionManager

if TYPE_CHECKING:
    from kondor.app.windows.windowmanager import WindowManager


def restored_contents(state: SessionWindow) -> WindowContents:
    return WindowContents(
        urls=[tab.url for tab in state.tabs],
        titles=[tab.title for tab in state.tabs],
        current_index=state.current_index,
    )


def should_restore_session() -> bool:
    return str(Settings.instance().property("startupBehavior")) == "restore"


def refuse_private_request(manager: WindowManager, message: SingleInstanceMessage) -> None:
    warn_private_refused()
    window = normal_window(manager)
    if window is not None:
        raise_window(window, message.activation_token)


def handle_single_instance_message(manager: WindowManager, message: SingleInstanceMessage) -> None:
    is_available = ProfileManager.instance().is_private_browsing_available()
    if message.private_mode and not is_available:
        refuse_private_request(manager, message)
        return
    urls = list(message.urls)
    packages = take_extension_packages(urls)
    window = show_packages(manager, packages, open_urls_for_launch(manager, message, urls))
    if window is not None:
        raise_window(window, message.activation_token)


def open_urls_for_launch(
    manager: WindowManager, message: SingleInstanceMessage, urls: list[QUrl]
) -> QObject | None:
    window = None if message.new_window else manager.window_for_request(message.private_mode)
    if window is None:
        return manager.create_window(WindowContents(is_private=message.private_mode, urls=urls))
    if urls:
        add_tabs(window, urls)
    return window


def add_tabs(window: QObject, urls: list[QUrl]) -> None:
    is_added = QMetaObject.invokeMethod(window, "openUrlsInNewTabs", Q_ARG("QVariant", urls))
    if not is_added:
        qWarning("Kondor: cannot add tabs to the running window")


def normal_window(manager: WindowManager) -> QObject | None:
    return manager.window_for_request(False) or manager.create_window(WindowContents())


def show_packages(
    manager: WindowManager, packages: list[str], window: QObject | None
) -> QObject | None:
    if not packages:
        return window
    normal = normal_window(manager)
    show_extension_package(normal, packages[0])
    return window or normal


def show_extension_package(window: QObject | None, path: str) -> None:
    ExtensionManager.instance().inspectFile(path)
    if window is None:
        return
    open_extensions_page(window)


def open_extensions_page(window: QObject) -> bool:
    page = Q_ARG("QVariant", "extensions")
    is_opened = bool(QMetaObject.invokeMethod(window, "openSettingsPage", page))
    if not is_opened:
        qWarning("Kondor: cannot open the extensions settings")
    return is_opened


def show_extensions_settings(manager: WindowManager) -> None:
    window = manager.window_for_request(False) or manager.window_for_request(True)
    if window is None:
        return
    if open_extensions_page(window):
        raise_window(window, b"")


def open_startup_windows(manager: WindowManager) -> None:
    urls = list(StartupArgs.instance().startup_urls())
    packages = take_extension_packages(urls)
    is_opened = open_restored_windows(manager)
    is_opened = open_command_line_window(manager, urls) or is_opened
    if not is_opened:
        manager.create_window(WindowContents())
    if packages:
        show_extension_package(manager.window_for_request(False), packages[0])


def open_restored_windows(manager: WindowManager) -> bool:
    if not should_restore_session():
        return False
    windows = SessionManager.instance().saved_windows()
    created = [manager.create_window(restored_contents(state)) for state in windows]
    return any(window is not None for window in created)


def open_command_line_window(manager: WindowManager, urls: list[QUrl]) -> bool:
    is_private = StartupArgs.instance().startup_private()
    if not urls and not is_private:
        return False
    return manager.create_window(WindowContents(is_private=is_private, urls=urls)) is not None
