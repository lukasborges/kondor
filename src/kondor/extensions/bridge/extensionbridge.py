from PySide6.QtCore import Property, QObject, Signal, Slot
from shiboken6 import isValid

from kondor.browser.tabs.tab import Tab
from kondor.extensions.bridge.bridgecalls import BridgeContext, handle_bridge_call
from kondor.extensions.bridge.extensioncall import ExtensionCall, error_reply
from kondor.extensions.bridge.extensionpageapi import ExtensionPageApi
from kondor.extensions.extensionmanager import ExtensionManager


class ExtensionBridge(QObject):
    tabChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tab: Tab | None = None
        self._api = ExtensionPageApi(self)

    def _get_tab(self) -> Tab | None:
        return self._tab if self._tab is not None and isValid(self._tab) else None

    def _set_tab(self, tab: Tab | None) -> None:
        if self._get_tab() is tab:
            return
        self._stop_watching_tab()
        self._tab = tab
        if tab is not None:
            tab.destroyed.connect(self._forget_tab)
        self.tabChanged.emit()

    def _stop_watching_tab(self) -> None:
        if self._get_tab() is not None and self._tab is not None:
            self._tab.destroyed.disconnect(self._forget_tab)

    @Slot()
    def _forget_tab(self) -> None:
        self._tab = None
        self.tabChanged.emit()

    tab = Property(Tab, _get_tab, _set_tab, notify=tabChanged)

    @Slot(result=QObject)
    def pageApi(self) -> QObject:
        return self._api

    def refusal_for(self, call: ExtensionCall) -> str:
        tab = self._get_tab()
        manager = ExtensionManager.instance()
        if tab is None:
            return error_reply("No tab")
        if not manager.check_token(call.extension_id, call.token):
            return error_reply("Invalid extension token")
        if not manager.is_active(call.extension_id, tab.isPrivate):
            return error_reply("The extension is turned off")
        return ""

    def request(self, call: ExtensionCall) -> str:
        refusal = self.refusal_for(call)
        tab = self._get_tab()
        if refusal or tab is None:
            return refusal
        return handle_bridge_call(BridgeContext(tab, call))
