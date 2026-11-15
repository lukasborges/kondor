from dataclasses import dataclass

from kondor.browser.tabs.tab import Tab
from kondor.extensions.bridge.extensioncall import ExtensionCall


@dataclass(frozen=True)
class BridgeContext:
    tab: Tab
    call: ExtensionCall
