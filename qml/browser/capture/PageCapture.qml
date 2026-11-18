import QtQuick
import QtQuick.Controls
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    readonly property real maximumHeight: 16384 / Screen.devicePixelRatio
    readonly property string metricsScript: "[Math.max(document.documentElement.scrollHeight, "
        + "document.body ? document.body.scrollHeight : 0), window.scrollY]"

    property real scrollTop: 0
    property int framesToWait: 0

    visible: false

    function captureVisibleArea() {
        webView.grabToImage(result => root.tab.setScreenshot(result))
    }

    function captureFullPage() {
        webView.runJavaScript(metricsScript, metrics => root.layOutFullPage(metrics))
    }

    function layOutFullPage(metrics) {
        scrollTop = metrics[1]
        const height = Math.min(metrics[0] * webView.zoomFactor, maximumHeight)
        webView.SplitView.fillHeight = false
        webView.SplitView.preferredHeight = height
        webView.SplitView.minimumHeight = height
        framesToWait = 2
        webView.Window.window.update()
    }

    function grabFullPage() {
        webView.grabToImage(result => root.restoreView(result))
    }

    function restoreView(result) {
        webView.SplitView.minimumHeight = 0
        webView.SplitView.fillHeight = true
        webView.runJavaScript("window.scrollTo(window.scrollX, " + scrollTop + ")")
        root.tab.setScreenshot(result)
    }

    function countFrame() {
        framesToWait -= 1
        if (framesToWait === 0)
            grabFullPage()
    }

    Connections {
        target: root.webView.Window.window
        enabled: root.framesToWait > 0
        function onFrameSwapped() { root.countFrame() }
    }

    Connections {
        target: root.tab
        function onScreenshotRequested(fullPage) {
            if (fullPage)
                root.captureFullPage()
            else
                root.captureVisibleArea()
        }
    }
}
