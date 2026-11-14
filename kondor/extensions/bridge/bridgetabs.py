from collections.abc import Callable

from PySide6.QtCore import QUrl

from kondor.browser.tabs.tab import Tab
from kondor.core.notifier import Notifier
from kondor.extensions.bridge.bridgecontext import BridgeContext
from kondor.extensions.bridge.extensioncall import (
    bool_argument,
    error_reply,
    ok_reply,
    string_argument,
)
from kondor.extensions.extensionmanager import ExtensionManager

TAB_COMMANDS: dict[str, Callable[[Tab], None]] = {
    "tabs.back": lambda tab: tab.goBack(),
    "tabs.forward": lambda tab: tab.goForward(),
    "tabs.reload": lambda tab: tab.reload(),
    "tabs.close": lambda tab: tab.closeTab(),
    "tabs.next": lambda tab: tab.selectNeighborTab(1),
    "tabs.previous": lambda tab: tab.selectNeighborTab(-1),
}


def is_web_address(url: QUrl) -> bool:
    return url.isValid() and url.scheme() in ("http", "https")


def web_address_of(context: BridgeContext) -> QUrl:
    return QUrl(string_argument(context.call, 0), QUrl.ParsingMode.StrictMode)


def run_tab_command(context: BridgeContext) -> str:
    command = TAB_COMMANDS.get(context.call.method)
    if command is not None:
        command(context.tab)
    return ok_reply()


def open_tab(context: BridgeContext) -> str:
    url = web_address_of(context)
    if not is_web_address(url):
        return error_reply("Only http and https addresses can be opened")
    context.tab.openTab(url, bool_argument(context.call, 1))
    return ok_reply()


def download(context: BridgeContext) -> str:
    url = web_address_of(context)
    if not is_web_address(url):
        return error_reply("Only http and https addresses can be downloaded")
    context.tab.downloadUrl(url, string_argument(context.call, 1))
    return ok_reply()


def notify(context: BridgeContext) -> str:
    call = context.call
    name = ExtensionManager.instance().display_name(call.extension_id)
    Notifier.instance().notify(
        f"{name}: {string_argument(call, 0)}", string_argument(call, 1), "preferences-plugin"
    )
    return ok_reply()
