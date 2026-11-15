from dataclasses import dataclass

from PySide6.QtCore import QDir, QFileInfo, QUrl

from kondor.browser.address.addressresolver import resolve_address
from kondor.core.settings.settings import Settings


@dataclass(frozen=True)
class StartupContext:
    working_directory: str
    home_page: QUrl
    search_template: str


def current_startup_context() -> StartupContext:
    settings = Settings.instance()
    home_page = QUrl(str(settings.property("homePage")))
    return StartupContext(QDir.currentPath(), home_page, settings.searchUrlTemplate())


def is_existing_file(text: str, working_directory: str) -> bool:
    return bool(QFileInfo.exists(QDir(working_directory).absoluteFilePath(text)))


def startup_url_for_argument(argument: str, context: StartupContext) -> QUrl:
    text = argument.strip()
    if not text:
        return QUrl()
    if is_existing_file(text, context.working_directory):
        return QUrl.fromUserInput(
            text, context.working_directory, QUrl.UserInputResolutionOption.AssumeLocalFile
        )
    return resolve_address(text, context.home_page, context.search_template)


def startup_urls_for_arguments(arguments: list[str]) -> list[QUrl]:
    context = current_startup_context()
    urls = [startup_url_for_argument(argument, context) for argument in arguments]
    return [url for url in urls if not url.isEmpty()]
