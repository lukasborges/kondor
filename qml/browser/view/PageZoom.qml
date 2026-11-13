import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    property string zoomHost: ""
    property bool applyingZoom: false

    visible: false

    function setViewZoom(factor) {
        if (Math.abs(webView.zoomFactor - factor) < 0.0001)
            return
        applyingZoom = true
        webView.zoomFactor = factor
        applyingZoom = false
    }

    function applySavedZoom(host) {
        zoomHost = host
        setViewZoom(host === "" ? 1.0 : ZoomManager.zoomFor(host))
    }

    function followUrl(url) {
        const host = ZoomManager.hostOf(url)
        if (host !== zoomHost)
            applySavedZoom(host)
    }

    function reapplySavedZoomAfterCommit(url) {
        applySavedZoom(ZoomManager.hostOf(url))
    }

    function saveZoomOfNormalTab(factor) {
        if (applyingZoom || tab.isPrivate || zoomHost === "")
            return
        ZoomManager.setZoomFor(zoomHost, factor)
    }

    Connections {
        target: ZoomManager
        function onZoomChanged(host, factor) {
            if (host === root.zoomHost)
                root.setViewZoom(factor)
        }
    }
}
