import QtQuick
import QtWebEngine
import Kondor

WebEngineView {
    id: root

    required property Tab tab
    required property TabModel tabModel
    required property PageZoom zoom
    required property ReaderMode reader
    required property PageOutput output
    required property CertificateErrorHandler certificates

    signal pageContextMenuRequested(var request)

    profile: root.tab.profile
    webChannelWorld: WebEngineScript.ApplicationWorld
    settings.fullScreenSupportEnabled: true

    function isStarted(status) {
        return status === WebEngineLoadingInfo.LoadStartedStatus
    }

    function updateTitle() {
        root.tab.setTitle(title)
        if (!root.tab.isPrivate && !root.tab.readerActive)
            HistoryManager.updateTitle(url, title)
    }

    function storeFavicon() {
        if (!root.tab.isPrivate && icon.toString() !== "")
            FaviconStore.store(url, icon)
    }

    function clearCrashOnStart(status) {
        if (isStarted(status))
            root.tab.setCrashed(false, "")
    }

    function updateTab(status) {
        root.tab.setLoading(isStarted(status))
        root.tab.setCanGoBack(canGoBack)
        root.tab.setCanGoForward(canGoForward)
    }

    function detectReaderOfPage() {
        if (!root.tab.newTabPage && url.toString() !== "about:blank")
            root.reader.detectReader()
    }

    function finishNormalLoad() {
        detectReaderOfPage()
        if (root.tab.isPrivate)
            return
        HistoryManager.addVisit(url, title)
        root.zoom.reapplySavedZoomAfterCommit(url)
    }

    function handleLoading(status) {
        clearCrashOnStart(status)
        root.reader.updateOnLoad(status)
        updateTab(status)
        if (!root.tab.readerActive && status === WebEngineLoadingInfo.LoadSucceededStatus)
            finishNormalLoad()
    }

    function terminationReason(status) {
        const reasons = {
            [WebEngineView.AbnormalTerminationStatus]: qsTr("The page's process ended unexpectedly."),
            [WebEngineView.CrashedTerminationStatus]: qsTr("The page crashed."),
            [WebEngineView.KilledTerminationStatus]: qsTr("The page's process was killed (possibly out of memory).")
        }
        return reasons[status] ?? ""
    }

    function showCrash(status, exitCode) {
        if (status === WebEngineView.NormalTerminationStatus)
            return
        root.tab.setLoading(false)
        root.tab.setCrashed(true, terminationReason(status), exitCode)
    }

    function acceptFullScreen(request) {
        request.accept()
        root.tab.setFullScreen(request.toggleOn)
    }

    function selectFirstScreen(request) {
        const screens = request.screensModel
        if (screens && screens.count > 0)
            request.selectScreen(screens.index(0, 0))
        else
            request.cancel()
    }

    function openRequestedWindow(request) {
        if (request.destination === WebEngineNewWindowRequest.InNewWindow)
            return WindowManager.newWindow(root.tab.isPrivate, [request.requestedUrl])
        const background = request.destination === WebEngineNewWindowRequest.InNewBackgroundTab
        root.tabModel.addTabWithProfile(root.tab.profile, request.requestedUrl, background)
    }

    onTitleChanged: updateTitle()
    onUrlChanged: {
        root.tab.setUrl(url)
        root.zoom.followUrl(url)
    }
    onZoomFactorChanged: {
        root.tab.setZoomFactor(zoomFactor)
        root.zoom.saveZoomOfNormalTab(zoomFactor)
    }
    onIconChanged: {
        root.tab.setIconUrl(icon)
        storeFavicon()
    }
    onLoadProgressChanged: root.tab.setProgress(loadProgress)
    onLoadingChanged: function(loadRequest) { handleLoading(loadRequest.status) }
    onCanGoBackChanged: root.tab.setCanGoBack(canGoBack)
    onCanGoForwardChanged: root.tab.setCanGoForward(canGoForward)
    onRenderProcessTerminated: function(status, exitCode) { showCrash(status, exitCode) }
    onFindTextFinished: function(result) {
        root.tab.setFindResult(result.numberOfMatches, result.activeMatch)
    }
    onFullScreenRequested: function(request) { acceptFullScreen(request) }
    onPermissionRequested: function(permission) { root.tab.permissions.enqueue(permission) }
    onContextMenuRequested: function(request) {
        request.accepted = true
        root.pageContextMenuRequested(request)
    }
    onPrintRequested: root.tab.print()
    onPdfPrintingFinished: function(filePath, success) { root.output.pdfFinished(filePath, success) }
    onCertificateError: function(error) { root.certificates.handle(error) }
    onDesktopMediaRequested: function(request) { selectFirstScreen(request) }
    onNewWindowRequested: function(request) { openRequestedWindow(request) }
}
