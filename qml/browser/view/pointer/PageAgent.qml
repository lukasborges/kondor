import QtQuick
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property Tab tab
    required property WebEngineView webView

    function publishTargetId() {
        root.tab.agent.setTargetId(root.webView.devToolsId)
    }

    anchors.fill: parent
    z: 1
    enabled: false
    Component.onCompleted: publishTargetId()

    Connections {
        target: root.webView
        function onLoadingChanged() { root.publishTargetId() }
    }

    Loader {
        anchors.fill: parent
        active: RemoteControl.active
        sourceComponent: AgentPointerOverlay {
            pointerColor: Kirigami.Theme.neutralTextColor
            webView: root.webView
        }
    }
}
