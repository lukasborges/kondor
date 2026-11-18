import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    visible: false

    function logPage(event) {
        ActionLog.pageEvent(root.tab, event)
    }

    function logLoading(info) {
        if (info.status === WebEngineLoadingInfo.LoadStartedStatus)
            ActionLog.navigationStarted(root.tab, info.url)
        else if (info.status === WebEngineLoadingInfo.LoadSucceededStatus)
            ActionLog.navigationFinished(root.tab)
        else if (info.status === WebEngineLoadingInfo.LoadFailedStatus)
            ActionLog.navigationFailed(root.tab, info.errorCode)
    }

    Connections {
        target: root.webView
        function onLoadingChanged(info) { root.logLoading(info) }
        function onRenderProcessTerminated(status) { root.logPage("render process terminated, status " + status) }
        function onContextMenuRequested() { root.logPage("context menu opened") }
        function onJavaScriptDialogRequested() { root.logPage("JavaScript dialog opened") }
        function onFileDialogRequested() { root.logPage("file dialog opened") }
        function onFullScreenRequested(request) {
            root.logPage(request.toggleOn ? "page full screen entered" : "page full screen left")
        }
    }

    Connections {
        target: root.tab.sleep
        function onSleepingChanged() { root.logPage(root.tab.sleep.sleeping ? "tab put to sleep" : "tab woken") }
    }
}
