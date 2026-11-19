import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    property string zoomHost: ""
    property bool applyingZoom: false
    readonly property real modeZoom: tab.responsive.ratio / Screen.devicePixelRatio

    visible: false

    function setViewZoom(factor) {
        if (Math.abs(webView.zoomFactor - factor) < 0.0001)
            return
        applyingZoom = true
        webView.zoomFactor = factor
        applyingZoom = false
    }

    function savedZoom(host) {
        return host === "" ? 1.0 : ZoomManager.zoomFor(host)
    }

    function wantedZoom() {
        return tab.responsive.isActive ? modeZoom : savedZoom(zoomHost)
    }

    function applySavedZoom(host) {
        zoomHost = host
        setViewZoom(wantedZoom())
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
        if (applyingZoom || tab.isPrivate || zoomHost === "" || tab.responsive.isActive)
            return
        ZoomManager.setZoomFor(zoomHost, factor)
    }

    onModeZoomChanged: setViewZoom(wantedZoom())

    Connections {
        target: root.tab.responsive
        function onActiveChanged() { root.setViewZoom(root.wantedZoom()) }
    }

    Connections {
        target: ZoomManager
        function onZoomChanged(host, factor) {
            if (host === root.zoomHost)
                root.setViewZoom(root.wantedZoom())
        }
    }
}
