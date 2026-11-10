import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel

    // Rejects the pending certificate request, if any, and drops the JS
    // reference. Returns true when there was one to answer.
    function rejectCertificateError() {
        if (!certificateErrorHolder.error)
            return false
        const error = certificateErrorHolder.error
        certificateErrorHolder.error = null
        error.rejectCertificate()
        return true
    }

    WebEngineView {
        id: webView
        anchors.fill: parent
        profile: root.tab.profile

        onTitleChanged: {
            root.tab.setTitle(title)
            if (!root.tab.isPrivate)
                HistoryManager.updateTitle(webView.url, title)
        }
        onUrlChanged: root.tab.setUrl(url)
        onIconChanged: {
            root.tab.setIconUrl(icon)
            // Only normal tabs persist a favicon: nothing from a private tab
            // may be written to disk.
            if (!root.tab.isPrivate && icon.toString() !== "")
                FaviconStore.store(webView.url, icon)
        }
        onLoadProgressChanged: root.tab.setProgress(loadProgress)

        onLoadingChanged: function(loadRequest) {
            root.tab.setLoading(loadRequest.status === WebEngineLoadingInfo.LoadStartedStatus)
            root.tab.setCanGoBack(webView.canGoBack)
            root.tab.setCanGoForward(webView.canGoForward)

            // Record the visit in history, for persistent tabs only.
            if (loadRequest.status === WebEngineLoadingInfo.LoadSucceededStatus
                    && !root.tab.isPrivate)
                HistoryManager.addVisit(webView.url, webView.title)
        }

        onCanGoBackChanged: root.tab.setCanGoBack(canGoBack)
        onCanGoForwardChanged: root.tab.setCanGoForward(canGoForward)

        onFindTextFinished: function(result) {
            root.tab.setFindResult(result.numberOfMatches, result.activeMatch)
        }

        // The page asked for full screen (a video player). Accept it and let
        // the window follow the tab; the player's button or Esc asks the page
        // to leave it, which arrives here again with toggleOn false.
        onFullScreenRequested: function(request) {
            request.accept()
            root.tab.setFullScreen(request.toggleOn)
        }

        // The page asked for a site permission (camera, microphone, location,
        // notifications, ...). The prompt belongs to this tab and is answered
        // through the Tab object, so switching tabs keeps it with the page.
        onPermissionRequested: function(permission) {
            root.tab.enqueuePermission(permission)
        }

        // A page failed the certificate check. Keep the request pending (defer)
        // so the error page can offer Back to Safety or an explicit override.
        onCertificateError: function(error) {
            if (!error.isMainFrame) {
                error.rejectCertificate()
                return
            }
            // A second error replaces the first one; answer the stale request.
            if (certificateErrorHolder.error)
                certificateErrorHolder.error.rejectCertificate()
            error.defer()
            certificateErrorHolder.error = error
            root.tab.setPendingCertificateError(error.url, error.description,
                                                error.overridable)
        }

        // Screen sharing: on Wayland Qt WebEngine uses the xdg-desktop-portal
        // picker itself. On X11 this signal selects a screen; without a
        // chooser, taking the first one is the minimal useful behavior.
        onDesktopMediaRequested: function(request) {
            const screens = request.screensModel
            if (screens && screens.count > 0)
                request.selectScreen(screens.index(0, 0))
            else
                request.cancel()
        }

        // A link with target=_blank / window.open opens in a new tab. The new
        // tab keeps the opener's profile, so private stays private (and keeps
        // its session) and background requests open in the background.
        onNewWindowRequested: function(request) {
            const background = request.destination === WebEngineNewWindowRequest.InNewBackgroundTab
            root.tabModel.addTabWithProfile(root.tab.profile, request.requestedUrl, background)
        }
    }

    // Holds the JS reference to the pending WebEngineCertificateError; the
    // value only stays answerable while this object keeps it.
    QtObject {
        id: certificateErrorHolder
        property var error: null
    }

    // Shown above the WebEngineView while the tab is on the New Tab page.
    NewTabPage {
        anchors.fill: parent
        visible: root.tab.newTabPage
        tab: root.tab
        tabModel: root.tabModel
    }

    CertificateErrorPage {
        anchors.fill: parent
        visible: root.tab.certificateErrorPending
        tab: root.tab
    }

    Connections {
        target: root.tab

        function onNavigationRequested(url) {
            rejectCertificateError()
            webView.url = url
        }
        // Back must return to the page that was on screen before.
        function onNewTabPageRequested() {
            rejectCertificateError()
            webView.url = "about:blank"
        }
        function onBackRequested() {
            // The toolbar Back answers the pending certificate request too.
            if (rejectCertificateError())
                root.tab.rejectCertificateError()
            if (webView.canGoBack)
                webView.goBack()
        }
        function onAcceptCertificateErrorRequested() {
            if (!certificateErrorHolder.error)
                return
            const error = certificateErrorHolder.error
            certificateErrorHolder.error = null
            error.acceptCertificate()
        }
        function onRejectCertificateErrorRequested() {
            if (!certificateErrorHolder.error)
                return
            const error = certificateErrorHolder.error
            certificateErrorHolder.error = null
            error.rejectCertificate()
            if (webView.canGoBack)
                webView.goBack()
            else if (root.tabModel.count > 1)
                root.tabModel.closeTabObject(root.tab)
            else
                root.tab.showNewTabPage()
        }
        function onForwardRequested() { if (webView.canGoForward) webView.goForward() }
        function onReloadRequested() { webView.reload() }
        function onStopRequested() { webView.stop() }
        function onZoomInRequested() { webView.zoomFactor = Math.min(5.0, webView.zoomFactor + 0.1) }
        function onZoomOutRequested() { webView.zoomFactor = Math.max(0.25, webView.zoomFactor - 0.1) }
        function onResetZoomRequested() { webView.zoomFactor = 1.0 }

        function onFindRequested(text, backward, caseSensitive) {
            let flags = 0
            if (backward)
                flags |= WebEngineView.FindBackward
            if (caseSensitive)
                flags |= WebEngineView.FindCaseSensitively
            webView.findText(text, flags)
        }
        function onStopFindRequested() { webView.findText("") }
        function onFocusPageRequested() { webView.forceActiveFocus() }
        function onExitFullScreenRequested() {
            webView.triggerWebAction(WebEngineView.ExitFullScreen)
        }
    }

    // Leaving the tab (switching or closing) ends its page's full screen, so
    // the window can go back to normal instead of staying full screen.
    onVisibleChanged: {
        if (!visible && root.tab.isFullScreen)
            root.tab.exitFullScreen()
    }

    Component.onCompleted: {
        if (root.tab.url.toString() !== "")
            webView.url = root.tab.url
    }
}
