import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel
    required property WebEngineView webView
    required property ReaderMode reader
    required property CertificateErrorHandler certificates

    visible: false

    function navigateTo(url) {
        certificates.rejectPending()
        webView.url = url
    }

    function goBack() {
        if (tab.readerActive)
            return reader.exitReader()
        if (certificates.rejectPending())
            tab.rejectCertificateError()
        if (webView.canGoBack)
            webView.goBack()
    }

    function findFlags(backward, caseSensitive) {
        let flags = 0
        if (backward)
            flags |= WebEngineView.FindBackward
        if (caseSensitive)
            flags |= WebEngineView.FindCaseSensitively
        return flags
    }

    function selectNeighborTab(delta) {
        const count = tabModel.count
        const index = tabModel.indexOfTab(tab)
        if (count > 1 && index >= 0)
            tabModel.setCurrentIndex((index + delta + count) % count)
    }

    function downloadUrl(url, fileName) {
        webView.runJavaScript(
            "(function(url, name) {"
            + "const a = document.createElement('a'); a.href = url;"
            + "if (name) a.download = name; a.style.display = 'none';"
            + "(document.body || document.documentElement).appendChild(a);"
            + "a.click(); a.remove(); })("
            + JSON.stringify(url.toString()) + ", " + JSON.stringify(fileName) + ");",
            WebEngineScript.ApplicationWorld)
    }

    function stepZoom(direction) {
        webView.zoomFactor = ZoomManager.step(webView.zoomFactor, direction)
    }

    Connections {
        target: root.tab

        function onNavigationRequested(url) { root.navigateTo(url) }
        function onNewTabPageRequested() { root.navigateTo("about:blank") }
        function onBackRequested() { root.goBack() }
        function onForwardRequested() { if (root.webView.canGoForward) root.webView.goForward() }
        function onReloadRequested() { root.webView.reload() }
        function onStopRequested() { root.webView.stop() }
        function onZoomInRequested() { root.stepZoom(1) }
        function onZoomOutRequested() { root.stepZoom(-1) }
        function onResetZoomRequested() { root.webView.zoomFactor = 1.0 }
        function onCloseRequested() { root.tabModel.closeTabObject(root.tab) }
        function onOpenTabRequested(url, background) {
            root.tabModel.addTabWithProfile(root.tab.profile, url, background)
        }
        function onNeighborTabRequested(delta) { root.selectNeighborTab(delta) }
        function onDownloadUrlRequested(url, fileName) { root.downloadUrl(url, fileName) }
        function onFindRequested(text, backward, caseSensitive) {
            root.webView.findText(text, root.findFlags(backward, caseSensitive))
        }
        function onStopFindRequested() { root.webView.findText("") }
        function onFocusPageRequested() { root.webView.forceActiveFocus() }
        function onExitFullScreenRequested() {
            root.webView.triggerWebAction(WebEngineView.ExitFullScreen)
        }
    }
}
