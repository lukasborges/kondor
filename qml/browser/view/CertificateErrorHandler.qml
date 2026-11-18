import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel
    required property WebEngineView webView

    property var pendingError: null

    PageLeaver {
        id: leaver
        tab: root.tab
        tabModel: root.tabModel
        webView: root.webView
    }

    visible: false

    function takePendingError() {
        const error = pendingError
        pendingError = null
        return error
    }

    function rejectPending() {
        const error = takePendingError()
        if (!error)
            return false
        error.rejectCertificate()
        return true
    }

    function holdMainFrameError(error) {
        if (pendingError)
            pendingError.rejectCertificate()
        error.defer()
        pendingError = error
        tab.security.setPendingCertificateError(error.url, error.description, error.overridable)
    }

    function handle(error) {
        if (error.isMainFrame && tab.security.failUpgradeOf(error.url))
            error.rejectCertificate()
        else if (error.isMainFrame)
            holdMainFrameError(error)
        else
            error.rejectCertificate()
    }

    Connections {
        target: root.tab.security

        function onAcceptCertificateErrorRequested() {
            const error = root.takePendingError()
            if (error)
                error.acceptCertificate()
        }

        function onRejectCertificateErrorRequested() {
            if (root.rejectPending())
                leaver.leave()
        }
    }
}
