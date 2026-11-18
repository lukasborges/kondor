import QtQuick
import QtWebEngine
import Kondor

Item {
    id: root

    required property Tab tab
    required property TabModel tabModel
    required property WebEngineView webView

    readonly property bool isWaiting: tab.security.upgradedFrom.toString() !== ""
        && tab.loading && tab.progress <= 10 && !tab.security.httpsOnlyWarningPending

    function failSlowUpgrade() {
        if (tab.security.failUpgradeOf(webView.url))
            webView.stop()
    }

    function leavePage() {
        if (webView.canGoBack)
            webView.goBack()
        else if (tabModel.count > 1)
            tabModel.closeTabObject(tab)
        else
            tab.showNewTabPage()
    }

    HttpsOnlyPage {
        anchors.fill: parent
        visible: root.tab.security.httpsOnlyWarningPending
        tab: root.tab
    }

    Timer {
        interval: 10000
        running: root.isWaiting
        onTriggered: root.failSlowUpgrade()
    }

    Connections {
        target: root.tab.security

        function onContinueToHttpRequested(url) { root.webView.url = url }
        function onLeaveHttpsOnlyWarningRequested() { root.leavePage() }
    }
}
