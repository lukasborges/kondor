import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    function isNavigationStart(info) {
        return info.status === WebEngineLoadingInfo.LoadStartedStatus
    }

    visible: false

    Binding {
        target: root.webView.settings
        property: "javascriptCanOpenWindows"
        value: !Settings.blockPopups || root.tab.popups.isAllowed
    }

    Connections {
        target: root.webView
        function onLoadingChanged(info) {
            if (root.isNavigationStart(info))
                root.tab.popups.clear()
        }
    }
}
