import QtQuick
import org.kde.kirigami as Kirigami
import Kondor

Rectangle {
    id: root

    required property TabResponsive responsive
    required property real fitScale
    required property bool isCentered
    property bool resizesWidth: false
    property bool resizesHeight: false
    property int cursor: Qt.SizeFDiagCursor

    property point pressPoint
    property size pressSize

    function scenePoint(mouse) {
        return mouseArea.mapToItem(null, mouse.x, mouse.y)
    }

    function widthAfter(point) {
        const factor = isCentered ? 2 : 1
        return resizesWidth ? pressSize.width + factor * (point.x - pressPoint.x) / fitScale : pressSize.width
    }

    function heightAfter(point) {
        return resizesHeight ? pressSize.height + (point.y - pressPoint.y) / fitScale : pressSize.height
    }

    function resizeTo(mouse) {
        const point = scenePoint(mouse)
        responsive.setSize(Math.round(widthAfter(point)), Math.round(heightAfter(point)))
    }

    radius: 2
    color: Kirigami.Theme.disabledTextColor

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        anchors.margins: -Kirigami.Units.smallSpacing
        cursorShape: root.cursor
        onPressed: function(mouse) {
            root.pressPoint = root.scenePoint(mouse)
            root.pressSize = Qt.size(root.responsive.width, root.responsive.height)
        }
        onPositionChanged: function(mouse) { root.resizeTo(mouse) }
    }
}
