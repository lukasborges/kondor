import os

import shiboken6
from PySide6.QtCore import qWarning
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from kondor.adblock.adblockmanager import AdBlockManager
from kondor.app.commandline.commandline import CommandLine
from kondor.app.commandline.startupargs import StartupArgs
from kondor.app.instance.singleinstance import SingleInstance, StartResult
from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.startup.appidentity import set_up_language_and_style
from kondor.app.startup.qmlregistry import register_all_types
from kondor.app.windows.windowmanager import WindowManager
from kondor.browser.favicons.faviconimageprovider import FaviconImageProvider
from kondor.browser.profile.profilemanager import ProfileManager
from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from kondor.extensions.install.extensionloader import ExtensionLoader

FAVICON_PROVIDER = "kondor-favicon"


def message_for(command_line: CommandLine) -> SingleInstanceMessage:
    return SingleInstanceMessage(
        urls=command_line.urls,
        private_mode=command_line.is_private,
        new_window=command_line.new_window,
        activation_token=os.environ.get("XDG_ACTIVATION_TOKEN", "").encode("utf-8"),
    )


def warn_about_separate_instance() -> None:
    qWarning(
        f"Kondor: cannot listen for later launches on {SingleInstance.server_name()}; "
        "running as a separate instance"
    )


def publish_startup_arguments(command_line: CommandLine) -> None:
    startup_args = StartupArgs.instance()
    startup_args.set_startup_urls(command_line.urls)
    startup_args.set_startup_private(command_line.is_private)


def register_profiles_with_extensions() -> None:
    extensions = ExtensionManager.instance()
    profiles = ProfileManager.instance()
    profiles.profileCreated.connect(extensions.register_profile)
    for profile in profiles.profiles():
        extensions.register_profile(profile)


def load_unpacked_extensions(app: QApplication, directories: list[str]) -> None:
    if not directories:
        return
    loader = ExtensionLoader(app)
    loader.load(ProfileManager.instance().defaultProfile(), directories)


def forwards_to_running_instance(
    single_instance: SingleInstance, command_line: CommandLine
) -> bool:
    if command_line.new_instance:
        return False
    result = single_instance.start(message_for(command_line))
    if result is StartResult.FAILED:
        warn_about_separate_instance()
    return result is StartResult.FORWARDED


def start_browser(app: QApplication, command_line: CommandLine) -> None:
    publish_startup_arguments(command_line)
    register_all_types()
    set_up_language_and_style(app)
    AdBlockManager.instance().start()
    register_profiles_with_extensions()
    load_unpacked_extensions(app, command_line.extension_directories)


def open_windows(engine: QQmlApplicationEngine, single_instance: SingleInstance) -> bool:
    engine.addImageProvider(FAVICON_PROVIDER, FaviconImageProvider())
    window_manager = WindowManager.instance()
    window_manager.set_engine(engine)
    single_instance.messageReceived.connect(window_manager.handle_single_instance_message)
    window_manager.open_startup_windows()
    ExtensionCatalog.instance().start_auto_update()
    return window_manager.window_count() > 0


def shut_down(engine: QQmlApplicationEngine) -> None:
    WindowManager.instance().release_windows()
    shiboken6.delete(engine)
