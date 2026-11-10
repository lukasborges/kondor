import QtQuick
import QtQuick.Controls
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel

    // Last page position a context menu was requested at, in the view's
    // coordinates. The Menu / Shift+F10 shortcut opens the menu there.
    property point contextMenuPosition: Qt.point(0, 0)

    // Temporary PDF being printed for the viewer, if any.
    property string printPath: ""

    function pdfFinished(filePath, success) {
        root.tab.setPdfFinished(filePath, success)
        if (filePath === root.printPath) {
            root.printPath = ""
            if (success)
                FileHelper.openFile(filePath)
            else
                Notifier.notify(qsTr("Print failed"), root.tab.title, "document-print")
        } else if (success) {
            Notifier.notify(qsTr("PDF saved"), filePath, "document-export")
        } else {
            Notifier.notify(qsTr("Saving the PDF failed"), filePath, "document-export")
        }
    }

    // Host whose saved zoom the view currently shows, and a guard so that
    // applying a saved zoom is not saved back.
    property string zoomHost: ""
    property bool applyingZoom: false

    function setViewZoom(factor) {
        if (Math.abs(webView.zoomFactor - factor) < 0.0001)
            return
        root.applyingZoom = true
        webView.zoomFactor = factor
        root.applyingZoom = false
    }

    function applySavedZoom(host) {
        root.zoomHost = host
        root.setViewZoom(host === "" ? 1.0 : ZoomManager.zoomFor(host))
    }

    Connections {
        target: ZoomManager
        function onZoomChanged(host, factor) {
            if (host === root.zoomHost)
                root.setViewZoom(factor)
        }
    }

    // --- Reader mode -------------------------------------------------------
    // The page's URL while the article is shown (loadHtml uses it as base URL).
    property url readerOriginalUrl: ""
    // True from loadHtml() until the article document finished loading, so its
    // own load events are not taken for a navigation.
    property bool readerLoadPending: false

    function readResource(name) {
        return FileHelper.readerResource(name)
    }

    function readerVars() {
        const family = Settings.readerSerif
            ? "'Noto Serif', 'DejaVu Serif', Georgia, serif"
            : "'Noto Sans', 'DejaVu Sans', system-ui, sans-serif"
        return "--reader-bg: " + readerColors.backgroundColor
            + "; --reader-text: " + readerColors.textColor
            + "; --reader-link: " + readerColors.linkColor
            + "; --reader-muted: " + readerColors.disabledTextColor
            + "; --reader-font: " + family
            + "; --reader-size: " + Settings.readerFontSize + "px;"
    }

    // Colors of the View color set (the page background of the app).
    Item {
        id: readerColors
        Kirigami.Theme.colorSet: Kirigami.Theme.View
        Kirigami.Theme.inherit: false
        readonly property color backgroundColor: Kirigami.Theme.backgroundColor
        readonly property color textColor: Kirigami.Theme.textColor
        readonly property color linkColor: Kirigami.Theme.linkColor
        readonly property color disabledTextColor: Kirigami.Theme.disabledTextColor
    }

    function applyReaderStyle() {
        if (!root.tab.readerActive || root.readerLoadPending)
            return
        const css = JSON.stringify(":root { " + root.readerVars() + " }")
        webView.runJavaScript(
            "document.getElementById('reader-vars').textContent = " + css + ";",
            WebEngineScript.ApplicationWorld)
    }

    Connections {
        target: Settings
        function onReaderFontSizeChanged() { root.applyReaderStyle() }
        function onReaderSerifChanged() { root.applyReaderStyle() }
    }
    Connections {
        target: readerColors
        function onBackgroundColorChanged() { root.applyReaderStyle() }
        function onTextColorChanged() { root.applyReaderStyle() }
        function onLinkColorChanged() { root.applyReaderStyle() }
    }

    function escapeHtml(text) {
        return String(text ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;")
            .replace(/>/g, "&gt;").replace(/"/g, "&quot;")
    }

    // Is the page an article? Runs after every successful normal load.
    function detectReader() {
        webView.runJavaScript(
            root.readResource("Readability-readerable.js")
                + "\n;isProbablyReaderable(document);",
            WebEngineScript.ApplicationWorld,
            function(result) { root.tab.setReaderAvailable(result === true) })
    }

    function enterReader() {
        const original = webView.url
        webView.runJavaScript(
            root.readResource("Readability.js") + "\n;(function() {"
                + "const a = new Readability(document.cloneNode(true)).parse();"
                + "return a ? { title: a.title, byline: a.byline, content: a.content,"
                + " siteName: a.siteName, lang: a.lang, dir: a.dir } : null; })();",
            WebEngineScript.ApplicationWorld,
            function(article) {
                if (!article || !article.content || webView.url !== original) {
                    root.tab.setReaderAvailable(false)
                    return
                }
                const values = {
                    lang: root.escapeHtml(article.lang || ""),
                    dir: root.escapeHtml(article.dir || "ltr"),
                    title: root.escapeHtml(article.title),
                    siteName: root.escapeHtml(article.siteName),
                    byline: root.escapeHtml(article.byline),
                    vars: root.readerVars(),
                    content: article.content
                }
                // One pass, so text inside the article is never substituted.
                const html = root.readResource("template.html")
                    .replace(/\{\{(\w+)\}\}/g, function(match, key) { return values[key] ?? "" })
                root.readerOriginalUrl = original
                root.readerLoadPending = true
                root.tab.setReaderActive(true)
                webView.loadHtml(html, original)
            })
    }

    function exitReader() {
        if (!root.tab.readerActive)
            return
        const original = root.readerOriginalUrl
        root.readerLoadPending = false
        root.tab.setReaderActive(false)
        webView.url = original
    }

    function setDevToolsOpen(open) {
        if (open === root.tab.devToolsOpen)
            return
        webView.devToolsView = open ? devTools : null
        root.tab.setDevToolsOpen(open)
    }

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

    // The page and, below it, Chromium DevTools while they are open. The
    // DevTools view shares the page's profile, so a private tab's DevTools
    // stay off the record.
    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        WebEngineView {
            id: webView
            SplitView.fillHeight: true
            profile: root.tab.profile

            // Qt WebEngine disables page full screen by default, so a video
            // player's button would never reach onFullScreenRequested.
            settings.fullScreenSupportEnabled: true

            onTitleChanged: {
                root.tab.setTitle(title)
                if (!root.tab.isPrivate && !root.tab.readerActive)
                    HistoryManager.updateTitle(webView.url, title)
            }
            onUrlChanged: {
                root.tab.setUrl(url)
                const host = ZoomManager.hostOf(url)
                if (host !== root.zoomHost)
                    root.applySavedZoom(host)
            }
            // Covers Ctrl+wheel, the zoom commands and the page itself.
            onZoomFactorChanged: {
                root.tab.setZoomFactor(zoomFactor)
                // Private tabs read the saved zoom but never write it.
                if (!root.applyingZoom && !root.tab.isPrivate && root.zoomHost !== "")
                    ZoomManager.setZoomFor(root.zoomHost, zoomFactor)
            }
            onIconChanged: {
                root.tab.setIconUrl(icon)
                // Only normal tabs persist a favicon: nothing from a private tab
                // may be written to disk.
                if (!root.tab.isPrivate && icon.toString() !== "")
                    FaviconStore.store(webView.url, icon)
            }
            onLoadProgressChanged: root.tab.setProgress(loadProgress)

            onLoadingChanged: function(loadRequest) {
                // A new load means the page has a renderer again; the crash page
                // goes away as soon as the reload starts.
                if (loadRequest.status === WebEngineLoadingInfo.LoadStartedStatus)
                    root.tab.setCrashed(false, "")

                // A navigation away from the article ends reader mode; the load
                // of the article itself (loadHtml) does not.
                if (loadRequest.status === WebEngineLoadingInfo.LoadStartedStatus
                        && root.tab.readerActive && !root.readerLoadPending) {
                    root.tab.setReaderActive(false)
                    root.tab.setReaderAvailable(false)
                } else if (loadRequest.status === WebEngineLoadingInfo.LoadStartedStatus
                        && !root.tab.readerActive) {
                    root.tab.setReaderAvailable(false)
                }
                const readerDocument = root.tab.readerActive
                if (readerDocument && loadRequest.status !== WebEngineLoadingInfo.LoadStartedStatus)
                    root.readerLoadPending = false

                root.tab.setLoading(loadRequest.status === WebEngineLoadingInfo.LoadStartedStatus)
                root.tab.setCanGoBack(webView.canGoBack)
                root.tab.setCanGoForward(webView.canGoForward)

                // Record the visit in history, for persistent tabs only.
                if (readerDocument)
                    return
                if (loadRequest.status === WebEngineLoadingInfo.LoadSucceededStatus
                        && !root.tab.newTabPage
                        && webView.url.toString() !== "about:blank")
                    root.detectReader()

                if (loadRequest.status === WebEngineLoadingInfo.LoadSucceededStatus
                        && !root.tab.isPrivate)
                    HistoryManager.addVisit(webView.url, webView.title)

                // Chromium may reset the zoom when the page commits. A private
                // tab keeps what the user set in it, so only normal tabs
                // re-apply the saved value.
                if (loadRequest.status === WebEngineLoadingInfo.LoadSucceededStatus
                        && !root.tab.isPrivate)
                    root.applySavedZoom(ZoomManager.hostOf(webView.url))
            }

            onCanGoBackChanged: root.tab.setCanGoBack(canGoBack)
            onCanGoForwardChanged: root.tab.setCanGoForward(canGoForward)

            // The renderer process died (crash, kill, out of memory). The view
            // stays blank until the user reloads, so this tab shows an
            // explanation; other tabs are not affected.
            onRenderProcessTerminated: function(terminationStatus, exitCode) {
                if (terminationStatus === WebEngineView.NormalTerminationStatus)
                    return
                const reasons = {
                    [WebEngineView.AbnormalTerminationStatus]: qsTr("The page's process ended unexpectedly."),
                    [WebEngineView.CrashedTerminationStatus]: qsTr("The page crashed."),
                    [WebEngineView.KilledTerminationStatus]: qsTr("The page's process was killed (possibly out of memory).")
                }
                root.tab.setLoading(false)
                root.tab.setCrashed(true, reasons[terminationStatus] ?? "", exitCode)
            }

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

            // Right click: take over from Qt WebEngine's minimal default menu and
            // show the full page menu at the cursor.
            onContextMenuRequested: function(request) {
                request.accepted = true
                root.contextMenuPosition = Qt.point(request.position.x, request.position.y)
                contextMenu.request = request
                contextMenu.popupAt(root.contextMenuPosition)
            }

            // A page failed the certificate check. Keep the request pending (defer)
            // so the error page can offer Back to Safety or an explicit override.
            // window.print() from the page.
            onPrintRequested: root.tab.print()

            onPdfPrintingFinished: function(filePath, success) { root.pdfFinished(filePath, success) }

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

            // A link with target=_blank / window.open opens in a new tab, unless
            // the page asked for a new window (shift+click): then the tab gets a
            // window of its own. The new tab or window keeps the opener's profile,
            // so private stays private (and keeps its session) and background
            // requests open in the background.
            onNewWindowRequested: function(request) {
                if (request.destination === WebEngineNewWindowRequest.InNewWindow) {
                    WindowManager.newWindow(root.tab.isPrivate, [request.requestedUrl])
                    return
                }
                const background = request.destination === WebEngineNewWindowRequest.InNewBackgroundTab
                root.tabModel.addTabWithProfile(root.tab.profile, request.requestedUrl, background)
            }
        }

        WebEngineView {
            id: devTools
            visible: root.tab.devToolsOpen
            SplitView.preferredHeight: root.height * 0.4
            SplitView.minimumHeight: 100
            profile: root.tab.profile

            // The "x" of the DevTools window.
            onWindowCloseRequested: root.setDevToolsOpen(false)
        }
    }

    // Right-click menu of the page. The Menu / Shift+F10 shortcut opens the
    // generic page menu at the last known position, or in the middle.
    PageContextMenu {
        id: contextMenu
        webView: webView
        tab: root.tab
        tabModel: root.tabModel
    }

    Shortcut {
        sequences: ["Menu", "Shift+F10"]
        enabled: root.visible && webView.activeFocus
        onActivated: {
            contextMenu.request = null
            const center = Qt.point(webView.width / 2, webView.height / 2)
            const point = root.contextMenuPosition.x === 0 && root.contextMenuPosition.y === 0
                ? center : root.contextMenuPosition
            contextMenu.popupAt(point)
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

    // Floating controls of reader mode.
    ReaderControls {
        anchors { right: parent.right; top: parent.top; margins: Kirigami.Units.largeSpacing }
        visible: root.tab.readerActive
        onExitRequested: root.exitReader()
    }

    CrashedPage {
        anchors.fill: parent
        visible: root.tab.crashed
        tab: root.tab
        tabModel: root.tabModel
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
        function onToggleReaderModeRequested() {
            if (root.tab.readerActive)
                root.exitReader()
            else
                root.enterReader()
        }
        function onBackRequested() {
            if (root.tab.readerActive) {
                root.exitReader()
                return
            }
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
        function onPrintToPdfRequested(filePath) {
            webView.printToPdf(filePath, WebEngineView.A4, WebEngineView.Portrait)
        }
        function onPrintRequested() {
            // No printer API in QML: render a temporary PDF and let the PDF
            // viewer print it.
            const path = FileHelper.tempPdfPath()
            if (path === "") {
                Notifier.notify(qsTr("Print failed"), root.tab.title, "document-print")
                return
            }
            root.printPath = path
            webView.printToPdf(path, WebEngineView.A4, WebEngineView.Portrait)
        }
        function onSavePageRequested(filePath, format) { webView.save(filePath, format) }
        function onToggleDevToolsRequested() { root.setDevToolsOpen(!root.tab.devToolsOpen) }
        function onInspectElementRequested() {
            root.setDevToolsOpen(true)
            webView.triggerWebAction(WebEngineView.InspectElement)
        }
        function onForwardRequested() { if (webView.canGoForward) webView.goForward() }
        function onReloadRequested() { webView.reload() }
        function onStopRequested() { webView.stop() }
        function onZoomInRequested() { webView.zoomFactor = ZoomManager.step(webView.zoomFactor, 1) }
        function onZoomOutRequested() { webView.zoomFactor = ZoomManager.step(webView.zoomFactor, -1) }
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

    // Leaving the tab (switching or closing) ends its page's full screen and
    // closes its context menu, so the window can go back to normal.
    onVisibleChanged: {
        if (visible)
            return
        contextMenu.close()
        if (root.tab && root.tab.isFullScreen)
            root.tab.exitFullScreen()
    }

    Component.onCompleted: {
        if (root.tab.url.toString() !== "")
            webView.url = root.tab.url
    }
}
