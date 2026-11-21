import QtQuick
import QtQuick.Window
import QtWebEngine

Item {
    id: root

    required property WebEngineView webView

    property int previousVisibility: Window.visibility

    visible: false

    function wasMinimized() {
        return previousVisibility === Window.Minimized
    }

    function repaint() {
        if (!webView.visible)
            return
        webView.visible = false
        webView.visible = true
    }

    function onWindowVisibilityChanged(visibility) {
        if (wasMinimized() && visibility !== Window.Hidden && visibility !== Window.Minimized)
            repaint()
        previousVisibility = visibility
    }

    // Qt WebEngine paints nothing after a restore until an event reaches the view:
    // https://github.com/lukasborges/kondor-browser/issues/221
    Connections {
        target: root.Window.window
        function onVisibilityChanged(visibility) { root.onWindowVisibilityChanged(visibility) }
    }
}
