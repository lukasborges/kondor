import QtQuick
import QtWebEngine
import org.kde.kirigami as Kirigami
import Kondor

Item {
    id: root

    required property AgentPointerBridge bridge
    required property WebEngineView webView
    required property color pointerColor

    property bool isShown: false
    property bool isGliding: false

    function viewPoint(x, y) {
        return Qt.point(x * root.webView.zoomFactor, y * root.webView.zoomFactor)
    }

    function moveTo(x, y) {
        const point = viewPoint(x, y)
        isGliding = isShown
        pointer.x = point.x
        pointer.y = point.y
        isShown = true
        fadeTimer.restart()
    }

    function clickAt(x, y) {
        ring.play(viewPoint(x, y))
    }

    clip: true
    enabled: false
    Accessible.ignored: true

    AgentPointerShape {
        id: pointer
        pointerColor: root.pointerColor
        opacity: root.isShown ? 1 : 0

        Behavior on x {
            enabled: root.isGliding
            NumberAnimation { duration: Kirigami.Units.shortDuration; easing.type: Easing.InOutQuad }
        }

        Behavior on y {
            enabled: root.isGliding
            NumberAnimation { duration: Kirigami.Units.shortDuration; easing.type: Easing.InOutQuad }
        }

        Behavior on opacity {
            NumberAnimation { duration: Kirigami.Units.longDuration }
        }
    }

    AgentClickRing {
        id: ring
        pointerColor: root.pointerColor
    }

    Timer {
        id: fadeTimer
        interval: 3000
        onTriggered: root.isShown = false
    }

    Connections {
        target: root.webView
        function onLoadingChanged(info) {
            if (info.status === WebEngineLoadingInfo.LoadStartedStatus)
                root.isShown = false
        }
    }

    Connections {
        target: root.bridge
        function onAgentMoved(x, y) { root.moveTo(x, y) }
        function onAgentPressed(x, y) { root.clickAt(x, y) }
    }
}
