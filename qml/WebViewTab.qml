import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel

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

        // The page asked for a site permission (camera, microphone, location,
        // notifications, ...). The prompt belongs to this tab and is answered
        // through the Tab object, so switching tabs keeps it with the page.
        onPermissionRequested: function(permission) {
            root.tab.enqueuePermission(permission)
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

    // Shown above the WebEngineView while the tab is on the New Tab page.
    NewTabPage {
        anchors.fill: parent
        visible: root.tab.newTabPage
        tab: root.tab
        tabModel: root.tabModel
    }

    Connections {
        target: root.tab

        function onNavigationRequested(url) { webView.url = url }
        // Back must return to the page that was on screen before.
        function onNewTabPageRequested() { webView.url = "about:blank" }
        function onBackRequested() { if (webView.canGoBack) webView.goBack() }
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
    }

    Component.onCompleted: {
        if (root.tab.url.toString() !== "")
            webView.url = root.tab.url
    }
}
